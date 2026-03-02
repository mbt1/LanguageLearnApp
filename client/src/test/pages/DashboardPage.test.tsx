// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { DashboardPage } from '@/pages/DashboardPage'

const mockUseAuth = vi.fn()

vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

// PasskeyManager calls listPasskeys on mount; VerifyEmailBanner uses resendVerification on click
vi.mock('@/api/auth', () => ({
  listPasskeys: vi.fn(),
  resendVerification: vi.fn(),
}))

import * as authApi from '@/api/auth'

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(authApi.listPasskeys).mockResolvedValue([])
  })

  it('shows verification banner for users with unverified email', async () => {
    mockUseAuth.mockReturnValue({
      user: { user_id: '1', email: 'unverified@example.com', email_verified: false },
      logout: vi.fn(),
    })

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText(/email not verified/i)).toBeInTheDocument()
  })

  it('hides verification banner for users with verified email', async () => {
    mockUseAuth.mockReturnValue({
      user: { user_id: '1', email: 'verified@example.com', email_verified: true },
      logout: vi.fn(),
    })

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    )

    // Wait for PasskeyManager async load to settle, then assert banner is absent
    await screen.findByText(/no passkeys registered/i)
    expect(screen.queryByText(/email not verified/i)).not.toBeInTheDocument()
  })
})
