// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { RegisterPage } from '@/pages/RegisterPage'

const mockUseAuth = vi.fn()

vi.mock('@/auth/AuthContext', () => ({
  // eslint-disable-next-line @typescript-eslint/no-unsafe-return
  useAuth: () => mockUseAuth(),
}))

describe('RegisterPage', () => {
  it('redirects authenticated user to dashboard', () => {
    mockUseAuth.mockReturnValue({
      user: { user_id: '1', email: 'test@example.com', email_verified: true },
      isLoading: false,
      login: vi.fn(),
      loginWithPasskey: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={['/register']}>
        <Routes>
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/" element={<div>dashboard</div>} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('dashboard')).toBeInTheDocument()
    expect(screen.queryByLabelText(/^email$/i)).not.toBeInTheDocument()
  })

  it('shows registration form when unauthenticated', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      login: vi.fn(),
      loginWithPasskey: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    )

    expect(screen.getByLabelText(/^email$/i)).toBeInTheDocument()
  })
})
