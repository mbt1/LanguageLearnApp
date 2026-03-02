// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { PasskeyManager } from '@/components/auth/PasskeyManager'
import { ApiError } from '@/api/client'

vi.mock('@/api/auth', () => ({
  listPasskeys: vi.fn(),
  deletePasskey: vi.fn(),
  getPasskeyRegistrationOptions: vi.fn(),
  verifyPasskeyRegistration: vi.fn(),
}))

import * as authApi from '@/api/auth'

describe('PasskeyManager', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows empty state when no passkeys are registered', async () => {
    vi.mocked(authApi.listPasskeys).mockResolvedValue([])

    render(<PasskeyManager />)

    expect(await screen.findByText(/no passkeys registered/i)).toBeInTheDocument()
  })

  it('shows passkey names after loading', async () => {
    vi.mocked(authApi.listPasskeys).mockResolvedValue([
      { id: 'pk-1', name: 'Work Laptop', created_at: '2026-01-15T10:00:00Z' },
      { id: 'pk-2', name: 'Phone', created_at: '2026-02-01T09:00:00Z' },
    ])

    render(<PasskeyManager />)

    expect(await screen.findByText('Work Laptop')).toBeInTheDocument()
    expect(screen.getByText('Phone')).toBeInTheDocument()
  })

  it('removes a passkey from the list when delete succeeds', async () => {
    vi.mocked(authApi.listPasskeys).mockResolvedValue([
      { id: 'pk-1', name: 'Old Key', created_at: '2026-01-01T00:00:00Z' },
    ])
    vi.mocked(authApi.deletePasskey).mockResolvedValue(undefined)

    render(<PasskeyManager />)
    await userEvent.click(await screen.findByRole('button', { name: /remove/i }))

    expect(screen.queryByText('Old Key')).not.toBeInTheDocument()
    expect(screen.getByText(/no passkeys registered/i)).toBeInTheDocument()
  })

  it('shows an error when delete fails', async () => {
    vi.mocked(authApi.listPasskeys).mockResolvedValue([
      { id: 'pk-1', name: 'My Key', created_at: '2026-01-01T00:00:00Z' },
    ])
    vi.mocked(authApi.deletePasskey).mockRejectedValue(new ApiError(404, 'Passkey not found'))

    render(<PasskeyManager />)
    await userEvent.click(await screen.findByRole('button', { name: /remove/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Passkey not found')
  })
})
