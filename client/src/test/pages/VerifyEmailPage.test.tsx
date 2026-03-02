// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { VerifyEmailPage } from '@/pages/VerifyEmailPage'

vi.mock('@/api/auth', () => ({
  verifyEmail: vi.fn(),
}))

import * as authApi from '@/api/auth'

describe('VerifyEmailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows error immediately when no token is present in the URL', () => {
    render(
      <MemoryRouter initialEntries={['/verify-email']}>
        <VerifyEmailPage />
      </MemoryRouter>,
    )

    expect(screen.getByText(/no verification token/i)).toBeInTheDocument()
    expect(authApi.verifyEmail).not.toHaveBeenCalled()
  })

  it('shows success message and login link after successful verification', async () => {
    vi.mocked(authApi.verifyEmail).mockResolvedValue({ message: 'Your email has been verified.' })

    render(
      <MemoryRouter initialEntries={['/verify-email?token=valid-token']}>
        <VerifyEmailPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText('Your email has been verified.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /go to login/i })).toBeInTheDocument()
  })

  it('shows failure message and back link when token is expired or invalid', async () => {
    vi.mocked(authApi.verifyEmail).mockRejectedValue(new Error('Expired'))

    render(
      <MemoryRouter initialEntries={['/verify-email?token=expired-token']}>
        <VerifyEmailPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText(/expired or invalid/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /back to login/i })).toBeInTheDocument()
  })
})
