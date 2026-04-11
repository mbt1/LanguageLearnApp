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
    // jsdom does not implement matchMedia
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
      })),
    })
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

  it('shows theme buttons defaulting to auto', () => {
    renderPage()
    const auto = screen.getByRole('button', { name: /auto/i })
    expect(auto).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: /light/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /dark/i })).toBeInTheDocument()
  })

  it('switches theme and stores preference', () => {
    renderPage()
    fireEvent.click(screen.getByRole('button', { name: /dark/i }))
    expect(localStorage.getItem('theme')).toBe('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)

    fireEvent.click(screen.getByRole('button', { name: /light/i }))
    expect(localStorage.getItem('theme')).toBe('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('migrates legacy darkMode key to theme', () => {
    localStorage.setItem('darkMode', 'true')
    renderPage()
    const dark = screen.getByRole('button', { name: /dark/i })
    expect(dark).toHaveAttribute('aria-pressed', 'true')
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

  it('shows review schedule toggle button', () => {
    renderPage()
    expect(screen.getByRole('button', { name: /show review schedule/i })).toBeInTheDocument()
  })

  it('toggles review schedule localStorage on click', () => {
    renderPage()
    const btn = screen.getByRole('button', { name: /show review schedule/i })

    fireEvent.click(btn)
    expect(localStorage.getItem('showReviewSchedule')).toBe('true')
    expect(screen.getByRole('button', { name: /hide review schedule/i })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /hide review schedule/i }))
    expect(localStorage.getItem('showReviewSchedule')).toBe('false')
  })

  it('reads review schedule preference from localStorage', () => {
    localStorage.setItem('showReviewSchedule', 'true')
    renderPage()
    expect(screen.getByRole('button', { name: /hide review schedule/i })).toBeInTheDocument()
  })
})
