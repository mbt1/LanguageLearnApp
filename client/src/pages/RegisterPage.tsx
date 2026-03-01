// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { Navigate } from 'react-router-dom'

import { useAuth } from '@/auth/AuthContext'
import { RegisterForm } from '@/components/auth/RegisterForm'

export function RegisterPage() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return <div className="flex h-screen items-center justify-center">Loading...</div>
  }

  if (user) {
    return <Navigate to="/" replace />
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <RegisterForm />
    </main>
  )
}
