// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider, useAuth } from '@/auth/AuthContext'

// Mock the auth API module
vi.mock('@/api/auth', () => ({
  register: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  refreshToken: vi.fn(),
  getPasskeyAuthenticationOptions: vi.fn(),
  verifyPasskeyAuthentication: vi.fn(),
}))

// Get mocked functions
const authApi = await vi.importMock<typeof import('@/api/auth')>('@/api/auth')

function TestConsumer() {
  const { user, isLoading, login, logout } = useAuth()
  return (
    <div>
      <p data-testid="loading">{String(isLoading)}</p>
      <p data-testid="user">{user ? user.email : 'none'}</p>
      <button onClick={() => void login('test@example.com', 'pass')}>Login</button>
      <button onClick={() => void logout()}>Logout</button>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('provides user after login', async () => {
    authApi.refreshToken.mockResolvedValueOnce(null)
    authApi.login.mockResolvedValueOnce({
      user_id: '1',
      email: 'test@example.com',
      email_verified: true,
    })

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false')
    })
    expect(screen.getByTestId('user').textContent).toBe('none')

    await act(async () => {
      await userEvent.click(screen.getByText('Login'))
    })

    expect(screen.getByTestId('user').textContent).toBe('test@example.com')
  })

  it('clears user on logout', async () => {
    authApi.refreshToken.mockResolvedValueOnce({
      user_id: '1',
      email: 'logged-in@example.com',
      email_verified: true,
    })
    authApi.logout.mockResolvedValueOnce(undefined)

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('user').textContent).toBe('logged-in@example.com')
    })

    await act(async () => {
      await userEvent.click(screen.getByText('Logout'))
    })

    expect(screen.getByTestId('user').textContent).toBe('none')
  })

  it('attempts refresh on mount', async () => {
    authApi.refreshToken.mockResolvedValueOnce({
      user_id: '1',
      email: 'restored@example.com',
      email_verified: false,
    })

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('user').textContent).toBe('restored@example.com')
    })
    expect(authApi.refreshToken).toHaveBeenCalledOnce()
  })

  it('handles failed refresh gracefully', async () => {
    authApi.refreshToken.mockResolvedValueOnce(null)

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false')
    })
    expect(screen.getByTestId('user').textContent).toBe('none')
  })
})
