// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { LoginForm } from '@/components/auth/LoginForm'
import { ApiError } from '@/api/client'

// Mock useAuth
const mockLogin = vi.fn()
const mockLoginWithPasskey = vi.fn()

vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => ({
    login: mockLogin,
    loginWithPasskey: mockLoginWithPasskey,
    user: null,
    isLoading: false,
    register: vi.fn(),
    logout: vi.fn(),
  }),
}))

function renderLoginForm() {
  return render(
    <MemoryRouter>
      <LoginForm />
    </MemoryRouter>,
  )
}

describe('LoginForm', () => {
  it('renders email and password fields', () => {
    renderLoginForm()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
  })

  it('calls login on submit', async () => {
    mockLogin.mockResolvedValueOnce(undefined)
    renderLoginForm()

    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com')
    await userEvent.type(screen.getByLabelText(/password/i), 'password123')
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }))

    expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'password123')
  })

  it('shows error on failed login', async () => {
    mockLogin.mockRejectedValueOnce(new ApiError(401, 'Invalid credentials'))
    renderLoginForm()

    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com')
    await userEvent.type(screen.getByLabelText(/password/i), 'wrong')
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid credentials')
  })

  it('has a link to register page', () => {
    renderLoginForm()
    expect(screen.getByRole('link', { name: /register/i })).toHaveAttribute('href', '/register')
  })

  it('can switch to passkey mode', async () => {
    renderLoginForm()
    await userEvent.click(screen.getByText(/use passkey instead/i))
    expect(screen.getByRole('button', { name: /login with passkey/i })).toBeInTheDocument()
  })
})
