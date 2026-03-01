// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { apiRequest, setAccessToken } from './client'
import type {
  LoginResponse,
  PasskeyAuthenticationVerifyResponse,
  PasskeyListItem,
  RefreshResponse,
  RegisterResponse,
  VerifyEmailResponse,
} from './types'

/* ── Types ─────────────────────────────────────────────────── */

/** Client-side user representation (extracted from JWT or response). */
export interface AuthUser {
  user_id: string
  email: string
  email_verified: boolean
}

export type { PasskeyListItem }

/* ── Email/password ────────────────────────────────────────── */

export async function register(
  email: string,
  password: string,
  displayName?: string,
): Promise<AuthUser> {
  const data = await apiRequest<RegisterResponse>('/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, display_name: displayName }),
  })
  setAccessToken(data.access_token)
  // Newly registered users are always unverified
  return { user_id: data.user_id, email: data.email, email_verified: false }
}

export async function login(email: string, password: string): Promise<AuthUser> {
  const data = await apiRequest<LoginResponse>('/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
  setAccessToken(data.access_token)
  return { user_id: data.user_id, email: data.email, email_verified: data.email_verified }
}

export async function logout(): Promise<void> {
  await apiRequest<undefined>('/v1/auth/logout', { method: 'POST' })
  setAccessToken(null)
}

export async function refreshToken(): Promise<AuthUser | null> {
  try {
    const data = await apiRequest<RefreshResponse>('/v1/auth/refresh', {
      method: 'POST',
    })
    setAccessToken(data.access_token)
    // Decode JWT payload to get user info (base64url → JSON)
    const parts = data.access_token.split('.')
    const encoded = parts[1]
    if (!encoded) throw new Error('Invalid token format')
    const payload = JSON.parse(atob(encoded)) as {
      sub: string
      email: string
      email_verified: boolean
    }
    return { user_id: payload.sub, email: payload.email, email_verified: payload.email_verified }
  } catch {
    setAccessToken(null)
    return null
  }
}

/* ── Email verification ────────────────────────────────────── */

export async function verifyEmail(token: string): Promise<VerifyEmailResponse> {
  return apiRequest<VerifyEmailResponse>(
    `/v1/auth/verify-email?token=${encodeURIComponent(token)}`,
  )
}

export async function resendVerification(): Promise<void> {
  await apiRequest<undefined>('/v1/auth/resend-verification', { method: 'POST' })
}

/* ── Passkeys ──────────────────────────────────────────────── */

export async function getPasskeyRegistrationOptions(): Promise<string> {
  const data = await apiRequest<{ options: string }>('/v1/auth/passkeys/register/options', {
    method: 'POST',
  })
  return data.options
}

export async function verifyPasskeyRegistration(credential: string, name: string): Promise<void> {
  await apiRequest<{ message: string }>('/v1/auth/passkeys/register/verify', {
    method: 'POST',
    body: JSON.stringify({ credential, name }),
  })
}

export async function getPasskeyAuthenticationOptions(email: string): Promise<string> {
  const data = await apiRequest<{ options: string }>('/v1/auth/passkeys/authenticate/options', {
    method: 'POST',
    body: JSON.stringify({ email }),
  })
  return data.options
}

export async function verifyPasskeyAuthentication(
  email: string,
  credential: string,
): Promise<AuthUser> {
  const data = await apiRequest<PasskeyAuthenticationVerifyResponse>(
    '/v1/auth/passkeys/authenticate/verify',
    {
      method: 'POST',
      body: JSON.stringify({ email, credential }),
    },
  )
  setAccessToken(data.access_token)
  return { user_id: data.user_id, email: data.email, email_verified: data.email_verified }
}

export async function listPasskeys(): Promise<PasskeyListItem[]> {
  return apiRequest<PasskeyListItem[]>('/v1/auth/passkeys/')
}

export async function deletePasskey(id: string): Promise<void> {
  await apiRequest<undefined>(`/v1/auth/passkeys/${id}`, { method: 'DELETE' })
}
