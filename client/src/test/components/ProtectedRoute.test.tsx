// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { ProtectedRoute } from '@/components/auth/ProtectedRoute'

const mockUseAuth =
  vi.fn<
    () => {
      user: { user_id: string; email: string; email_verified: boolean } | null
      isLoading: boolean
    }
  >()

vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

describe('ProtectedRoute', () => {
  it('redirects to /login when not authenticated', () => {
    mockUseAuth.mockReturnValue({ user: null, isLoading: false })

    render(
      <MemoryRouter initialEntries={['/']}>
        <ProtectedRoute>
          <p>Protected content</p>
        </ProtectedRoute>
      </MemoryRouter>,
    )

    expect(screen.queryByText('Protected content')).not.toBeInTheDocument()
  })

  it('shows children when authenticated', () => {
    mockUseAuth.mockReturnValue({
      user: { user_id: '1', email: 'test@example.com', email_verified: true },
      isLoading: false,
    })

    render(
      <MemoryRouter>
        <ProtectedRoute>
          <p>Protected content</p>
        </ProtectedRoute>
      </MemoryRouter>,
    )

    expect(screen.getByText('Protected content')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    mockUseAuth.mockReturnValue({ user: null, isLoading: true })

    render(
      <MemoryRouter>
        <ProtectedRoute>
          <p>Protected content</p>
        </ProtectedRoute>
      </MemoryRouter>,
    )

    expect(screen.getByText('Loading...')).toBeInTheDocument()
    expect(screen.queryByText('Protected content')).not.toBeInTheDocument()
  })
})
