# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from psycopg import AsyncConnection
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes
from webauthn.helpers.exceptions import (
    InvalidAuthenticationResponse,
    InvalidRegistrationResponse,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from auth.config import get_config
from auth.dependencies import get_current_user
from auth.schemas import (
    CurrentUser,
    PasskeyAuthenticationOptionsRequest,
    PasskeyAuthenticationOptionsResponse,
    PasskeyAuthenticationVerifyRequest,
    PasskeyAuthenticationVerifyResponse,
    PasskeyListItem,
    PasskeyRegistrationOptionsResponse,
    PasskeyRegistrationVerifyRequest,
    PasskeyRegistrationVerifyResponse,
)
from auth.tokens import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from auth.webauthn_store import challenge_store
from db.pool import get_conn
from db.queries.auth_tokens import create_refresh_token
from db.queries.passkeys import (
    create_passkey,
    delete_passkey,
    get_passkey_by_credential_id,
    list_passkeys_for_user,
    update_passkey_sign_count,
)
from db.queries.users import get_user_by_email

router = APIRouter(prefix="/v1/auth/passkeys", tags=["passkeys"])


def _set_refresh_cookie(response: Response, token: str, max_age: int) -> None:
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/v1/auth",
        max_age=max_age,
    )


@router.post("/register/options", response_model=PasskeyRegistrationOptionsResponse)
async def passkey_registration_options(
    conn: Annotated[AsyncConnection, Depends(get_conn)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> PasskeyRegistrationOptionsResponse:
    """Generate WebAuthn registration options for authenticated user."""
    config = get_config()
    existing = await list_passkeys_for_user(conn, user_id=current_user.user_id)
    exclude_credentials = [
        PublicKeyCredentialDescriptor(id=pk["credential_id"]) for pk in existing
    ]
    options = generate_registration_options(
        rp_id=config.rp_id,
        rp_name=config.rp_name,
        user_name=current_user.email,
        user_id=str(current_user.user_id).encode(),
        exclude_credentials=exclude_credentials,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )
    challenge_store.store(
        f"reg:{current_user.user_id}",
        options.challenge,
        str(current_user.user_id),
    )
    return PasskeyRegistrationOptionsResponse(options=options_to_json(options))


@router.post("/register/verify", response_model=PasskeyRegistrationVerifyResponse)
async def passkey_registration_verify(
    body: PasskeyRegistrationVerifyRequest,
    conn: Annotated[AsyncConnection, Depends(get_conn)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> PasskeyRegistrationVerifyResponse:
    """Verify WebAuthn registration response and store credential."""
    config = get_config()
    stored = challenge_store.pop(f"reg:{current_user.user_id}")
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending registration challenge",
        )
    try:
        verification = verify_registration_response(
            credential=json.loads(body.credential),
            expected_challenge=stored.challenge,
            expected_rp_id=config.rp_id,
            expected_origin=config.rp_origin,
        )
    except InvalidRegistrationResponse as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration verification failed: {exc}",
        ) from None

    await create_passkey(
        conn,
        user_id=current_user.user_id,
        credential_id=verification.credential_id,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        name=body.name,
    )
    await conn.commit()
    return PasskeyRegistrationVerifyResponse(message="Passkey registered successfully")


@router.post("/authenticate/options", response_model=PasskeyAuthenticationOptionsResponse)
async def passkey_authentication_options(
    body: PasskeyAuthenticationOptionsRequest,
    conn: Annotated[AsyncConnection, Depends(get_conn)],
) -> PasskeyAuthenticationOptionsResponse:
    """Generate WebAuthn authentication options for a user (public endpoint)."""
    config = get_config()
    user = await get_user_by_email(conn, email=body.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No passkeys registered for this email",
        )
    passkeys = await list_passkeys_for_user(conn, user_id=user["id"])
    if not passkeys:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No passkeys registered for this email",
        )
    allow_credentials = [
        PublicKeyCredentialDescriptor(id=pk["credential_id"]) for pk in passkeys
    ]
    options = generate_authentication_options(
        rp_id=config.rp_id,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    challenge_store.store(f"auth:{body.email}", options.challenge, body.email)
    return PasskeyAuthenticationOptionsResponse(options=options_to_json(options))


@router.post("/authenticate/verify", response_model=PasskeyAuthenticationVerifyResponse)
async def passkey_authentication_verify(
    body: PasskeyAuthenticationVerifyRequest,
    response: Response,
    conn: Annotated[AsyncConnection, Depends(get_conn)],
) -> PasskeyAuthenticationVerifyResponse:
    """Verify WebAuthn authentication response and issue tokens."""
    config = get_config()
    stored = challenge_store.pop(f"auth:{body.email}")
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending authentication challenge",
        )

    # Parse credential to get credential_id
    cred_data = json.loads(body.credential)
    raw_id = cred_data.get("rawId") or cred_data.get("id", "")

    # Look up the credential in our DB
    credential_id_bytes = base64url_to_bytes(raw_id)
    stored_passkey = await get_passkey_by_credential_id(
        conn, credential_id=credential_id_bytes
    )
    if stored_passkey is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown credential",
        )

    try:
        verification = verify_authentication_response(
            credential=cred_data,
            expected_challenge=stored.challenge,
            expected_rp_id=config.rp_id,
            expected_origin=config.rp_origin,
            credential_public_key=stored_passkey["public_key"],
            credential_current_sign_count=stored_passkey["sign_count"],
        )
    except InvalidAuthenticationResponse as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication verification failed: {exc}",
        ) from None

    # Update sign count
    await update_passkey_sign_count(
        conn,
        credential_id=verification.credential_id,
        sign_count=verification.new_sign_count,
    )

    # Get user and issue tokens
    user = await get_user_by_email(conn, email=body.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    access_token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        email_verified=user["email_verified"],
        secret=config.jwt_secret,
        algorithm=config.jwt_algorithm,
        expires_minutes=config.access_token_expire_minutes,
    )
    refresh_tok = generate_refresh_token()
    expires_at = datetime.now(UTC) + timedelta(days=config.refresh_token_expire_days)
    await create_refresh_token(
        conn,
        user_id=user["id"],
        token_hash=hash_refresh_token(refresh_tok),
        expires_at=expires_at,
    )
    _set_refresh_cookie(response, refresh_tok, config.refresh_token_expire_days * 86400)
    await conn.commit()

    return PasskeyAuthenticationVerifyResponse(
        user_id=user["id"],
        email=user["email"],
        email_verified=user["email_verified"],
        access_token=access_token,
    )


@router.get("/", response_model=list[PasskeyListItem])
async def list_passkeys(
    conn: Annotated[AsyncConnection, Depends(get_conn)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> list[PasskeyListItem]:
    """List user's registered passkeys."""
    passkeys = await list_passkeys_for_user(conn, user_id=current_user.user_id)
    return [
        PasskeyListItem(
            id=pk["id"],
            name=pk["name"],
            created_at=str(pk["created_at"]),
        )
        for pk in passkeys
    ]


@router.delete("/{passkey_id}", status_code=204)
async def remove_passkey(
    passkey_id: UUID,
    conn: Annotated[AsyncConnection, Depends(get_conn)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> None:
    """Remove a passkey (must belong to current user)."""
    deleted = await delete_passkey(conn, passkey_id=passkey_id, user_id=current_user.user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passkey not found",
        )
    await conn.commit()
