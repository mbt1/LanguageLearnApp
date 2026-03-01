// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, apiRequest, getAccessToken, setAccessToken } from '@/api/client'

// Mock global fetch
const fetchMock = vi.fn()
vi.stubGlobal('fetch', fetchMock)

function jsonResponse(data: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: 'OK',
    json: () => Promise.resolve(data),
    headers: new Headers(),
  } as Response
}

describe('apiRequest', () => {
  beforeEach(() => {
    setAccessToken(null)
    fetchMock.mockReset()
  })

  afterEach(() => {
    setAccessToken(null)
  })

  it('adds Authorization header when token is set', async () => {
    setAccessToken('test-token')
    fetchMock.mockResolvedValueOnce(jsonResponse({ ok: true }))

    await apiRequest('/v1/test')

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    const headers = options.headers as Headers
    expect(headers.get('Authorization')).toBe('Bearer test-token')
  })

  it('omits Authorization header when no token', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ ok: true }))

    await apiRequest('/v1/test')

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    const headers = options.headers as Headers
    expect(headers.get('Authorization')).toBeNull()
  })

  it('includes credentials for cookies', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ ok: true }))

    await apiRequest('/v1/test')

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(options.credentials).toBe('include')
  })

  it('attempts refresh on 401 and retries', async () => {
    setAccessToken('old-token')
    // First call: 401
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: 'Expired' }, 401))
    // Refresh call: success
    fetchMock.mockResolvedValueOnce(jsonResponse({ access_token: 'new-token' }))
    // Retry call: success
    fetchMock.mockResolvedValueOnce(jsonResponse({ data: 'success' }))

    const result = await apiRequest<{ data: string }>('/v1/test')

    expect(result.data).toBe('success')
    expect(getAccessToken()).toBe('new-token')
    expect(fetchMock).toHaveBeenCalledTimes(3)
  })

  it('throws ApiError on non-401 errors', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: 'Not found' }, 404))

    const error = await apiRequest('/v1/test').catch((e: unknown) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect((error as ApiError).status).toBe(404)
    expect((error as ApiError).detail).toBe('Not found')
  })

  it('returns undefined for 204 responses', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      status: 204,
      statusText: 'No Content',
      json: () => Promise.reject(new Error('no body')),
      headers: new Headers(),
    } as Response)

    const result = await apiRequest('/v1/test')
    expect(result).toBeUndefined()
  })
})
