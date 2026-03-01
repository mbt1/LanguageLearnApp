// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

// Mock the auth API — refreshToken returns null (no session)
vi.mock('@/api/auth', () => ({
  refreshToken: vi.fn().mockResolvedValue(null),
  register: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  getPasskeyAuthenticationOptions: vi.fn(),
  verifyPasskeyAuthentication: vi.fn(),
}))

import App from '../App'

describe('App', () => {
  it('renders the login page when not authenticated', async () => {
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('Login')).toBeInTheDocument()
    })
  })
})
