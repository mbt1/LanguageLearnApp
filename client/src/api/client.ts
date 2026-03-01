// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

/**
 * HTTP client with JWT access-token management.
 *
 * - Stores the access token in a module-level variable (JS memory only).
 * - Automatically adds `Authorization: Bearer <token>` header.
 * - Sends cookies (`credentials: "include"`) for the refresh-token flow.
 * - On a 401 response, attempts a single silent refresh before retrying.
 */

let accessToken: string | null = null

export function setAccessToken(token: string | null): void {
  accessToken = token
}

export function getAccessToken(): string | null {
  return accessToken
}

export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

async function parseError(resp: Response): Promise<ApiError> {
  try {
    const body = (await resp.json()) as { detail?: string }
    return new ApiError(resp.status, body.detail ?? resp.statusText)
  } catch {
    return new ApiError(resp.status, resp.statusText)
  }
}

async function refreshAccessToken(): Promise<boolean> {
  try {
    const resp = await fetch('/v1/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    })
    if (!resp.ok) return false
    const data = (await resp.json()) as { access_token: string }
    setAccessToken(data.access_token)
    return true
  } catch {
    return false
  }
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`)
  }
  if (options.body && typeof options.body === 'string' && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const resp = await fetch(path, {
    ...options,
    headers,
    credentials: 'include',
  })

  if (resp.status === 401 && accessToken) {
    // Attempt silent refresh once
    const refreshed = await refreshAccessToken()
    if (refreshed) {
      headers.set('Authorization', `Bearer ${accessToken}`)
      const retry = await fetch(path, {
        ...options,
        headers,
        credentials: 'include',
      })
      if (retry.ok) {
        if (retry.status === 204) return undefined as T
        return (await retry.json()) as T
      }
      const err = await parseError(retry)
      throw err
    }
    // Refresh failed — clear token
    setAccessToken(null)
    const err = await parseError(resp)
    throw err
  }

  if (!resp.ok) {
    const err = await parseError(resp)
    throw err
  }

  if (resp.status === 204) return undefined as T
  return (await resp.json()) as T
}
