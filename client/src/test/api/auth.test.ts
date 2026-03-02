// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/client', () => ({
  apiRequest: vi.fn(),
  setAccessToken: vi.fn(),
}))

import { login, refreshToken, register } from '@/api/auth'
import { apiRequest, setAccessToken } from '@/api/client'

const mockApiRequest = vi.mocked(apiRequest)
const mockSetToken = vi.mocked(setAccessToken)

/** Build a fake JWT with a base64-encoded JSON payload. */
function makeJwt(sub: string, email: string, email_verified: boolean): string {
  const payload = btoa(JSON.stringify({ sub, email, email_verified }))
  return `header.${payload}.sig`
}

describe('refreshToken', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('decodes JWT payload and returns user fields', async () => {
    mockApiRequest.mockResolvedValueOnce({
      access_token: makeJwt('user-1', 'test@example.com', true),
    })

    const user = await refreshToken()

    expect(user).toEqual({
      user_id: 'user-1',
      email: 'test@example.com',
      email_verified: true,
    })
  })

  it('returns null and clears token when the API call fails', async () => {
    mockApiRequest.mockRejectedValueOnce(new Error('Network error'))

    const user = await refreshToken()

    expect(user).toBeNull()
    expect(mockSetToken).toHaveBeenCalledWith(null)
  })
})

describe('register', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('always returns email_verified: false regardless of server response', async () => {
    mockApiRequest.mockResolvedValueOnce({
      access_token: 'token',
      user_id: 'user-1',
      email: 'new@example.com',
    })

    const user = await register('new@example.com', 'password123')

    expect(user.email_verified).toBe(false)
  })
})

describe('login', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('passes email_verified through from server response', async () => {
    mockApiRequest.mockResolvedValueOnce({
      access_token: 'token',
      user_id: 'user-1',
      email: 'user@example.com',
      email_verified: true,
    })

    const user = await login('user@example.com', 'password123')

    expect(user.email_verified).toBe(true)
  })
})
