// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { SettingsPage } from '@/pages/SettingsPage'

vi.mock('@/api/auth', () => ({
  listPasskeys: vi.fn(),
  deletePasskey: vi.fn(),
  getPasskeyRegistrationOptions: vi.fn(),
  verifyPasskeyRegistration: vi.fn(),
}))

import * as authApi from '@/api/auth'

function renderPage() {
  return render(
    <MemoryRouter>
      <SettingsPage />
    </MemoryRouter>,
  )
}

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(authApi.listPasskeys).mockResolvedValue([])
    localStorage.clear()
  })

  it('shows session size slider', () => {
    renderPage()
    expect(screen.getByRole('slider', { name: /session size/i })).toBeInTheDocument()
  })

  it('defaults to 20 when no stored preference', () => {
    renderPage()
    const slider = screen.getByRole('slider', { name: /session size/i })
    expect(slider).toHaveValue('20')
  })

  it('reads session size from localStorage', () => {
    localStorage.setItem('sessionSize', '30')
    renderPage()
    const slider = screen.getByRole('slider', { name: /session size/i })
    expect(slider).toHaveValue('30')
  })

  it('shows passkeys section', async () => {
    renderPage()
    expect(await screen.findByText(/no passkeys registered/i)).toBeInTheDocument()
  })

  it('shows theme toggle button', () => {
    renderPage()
    expect(
      screen.getByRole('button', { name: /switch to (dark|light) mode/i }),
    ).toBeInTheDocument()
  })

  it('updates session size label when slider changes', () => {
    renderPage()
    const slider = screen.getByRole('slider', { name: /session size/i })
    // fireEvent.change works on range inputs; userEvent.clear does not
    fireEvent.change(slider, { target: { value: '50' } })
    expect(slider).toHaveValue('50')
    // The value is also shown in a sibling span
    expect(screen.getByText('50')).toBeInTheDocument()
  })
})
