// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { RegisterForm } from '@/components/auth/RegisterForm'
import { ApiError } from '@/api/client'

const mockRegister = vi.fn()

vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => ({
    register: mockRegister,
    login: vi.fn(),
    loginWithPasskey: vi.fn(),
    user: null,
    isLoading: false,
    logout: vi.fn(),
  }),
}))

function renderRegisterForm() {
  return render(
    <MemoryRouter>
      <RegisterForm />
    </MemoryRouter>,
  )
}

describe('RegisterForm', () => {
  it('renders all fields', () => {
    renderRegisterForm()
    expect(screen.getByLabelText(/^email$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/display name/i)).toBeInTheDocument()
  })

  it('shows error for short password', async () => {
    renderRegisterForm()

    await userEvent.type(screen.getByLabelText(/^email$/i), 'test@example.com')
    await userEvent.type(screen.getByLabelText(/^password$/i), 'short')
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'short')
    await userEvent.click(screen.getByRole('button', { name: /create account/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent('at least 8 characters')
  })

  it('shows error for mismatched passwords', async () => {
    renderRegisterForm()

    await userEvent.type(screen.getByLabelText(/^email$/i), 'test@example.com')
    await userEvent.type(screen.getByLabelText(/^password$/i), 'password123')
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'differentpass')
    await userEvent.click(screen.getByRole('button', { name: /create account/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent('do not match')
  })

  it('calls register on valid submit', async () => {
    mockRegister.mockResolvedValueOnce(undefined)
    renderRegisterForm()

    await userEvent.type(screen.getByLabelText(/^email$/i), 'test@example.com')
    await userEvent.type(screen.getByLabelText(/^password$/i), 'password123')
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'password123')
    await userEvent.click(screen.getByRole('button', { name: /create account/i }))

    expect(mockRegister).toHaveBeenCalledWith('test@example.com', 'password123', undefined)
  })

  it('shows API error on duplicate email', async () => {
    mockRegister.mockRejectedValueOnce(new ApiError(409, 'Email already registered'))
    renderRegisterForm()

    await userEvent.type(screen.getByLabelText(/^email$/i), 'dup@example.com')
    await userEvent.type(screen.getByLabelText(/^password$/i), 'password123')
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'password123')
    await userEvent.click(screen.getByRole('button', { name: /create account/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Email already registered')
  })

  it('has a link to login page', () => {
    renderRegisterForm()
    expect(screen.getByRole('link', { name: /login/i })).toHaveAttribute('href', '/login')
  })
})
