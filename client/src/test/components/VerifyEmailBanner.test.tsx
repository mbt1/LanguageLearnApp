// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { VerifyEmailBanner } from '@/components/auth/VerifyEmailBanner'
import { ApiError } from '@/api/client'

vi.mock('@/api/auth', () => ({
  resendVerification: vi.fn(),
}))

import * as authApi from '@/api/auth'

describe('VerifyEmailBanner', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows confirmation text after a successful resend', async () => {
    vi.mocked(authApi.resendVerification).mockResolvedValue(undefined)

    render(<VerifyEmailBanner />)
    await userEvent.click(screen.getByRole('button', { name: /resend verification/i }))

    expect(await screen.findByText(/verification email sent/i)).toBeInTheDocument()
  })

  it('shows the API error message when resend is rejected with ApiError', async () => {
    vi.mocked(authApi.resendVerification).mockRejectedValue(
      new ApiError(429, 'Too many requests. Please wait before trying again.'),
    )

    render(<VerifyEmailBanner />)
    await userEvent.click(screen.getByRole('button', { name: /resend verification/i }))

    expect(await screen.findByText(/too many requests/i)).toBeInTheDocument()
  })

  it('shows a generic error message for unexpected failures', async () => {
    vi.mocked(authApi.resendVerification).mockRejectedValue(new Error('Network failure'))

    render(<VerifyEmailBanner />)
    await userEvent.click(screen.getByRole('button', { name: /resend verification/i }))

    expect(await screen.findByText(/failed to resend/i)).toBeInTheDocument()
  })
})
