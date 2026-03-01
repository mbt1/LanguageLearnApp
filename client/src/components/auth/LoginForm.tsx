// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { ApiError } from '@/api/client'

function getErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof ApiError) return err.detail
  return fallback
}

export function LoginForm() {
  const { login, loginWithPasskey } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [mode, setMode] = useState<'password' | 'passkey'>('password')

  async function handlePasswordLogin(e: React.SyntheticEvent) {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await login(email, password)
    } catch (err) {
      setError(getErrorMessage(err, 'Login failed'))
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handlePasskeyLogin(e: React.SyntheticEvent) {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await loginWithPasskey(email)
    } catch (err) {
      setError(getErrorMessage(err, 'Passkey login failed'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Card className="mx-auto w-full max-w-sm">
      <CardHeader>
        <CardTitle>Login</CardTitle>
        <CardDescription>Sign in to your account</CardDescription>
      </CardHeader>
      <CardContent>
        {error && (
          <p className="text-destructive mb-4 text-sm" role="alert">
            {error}
          </p>
        )}

        {mode === 'password' ? (
          <form
            onSubmit={(e) => {
              void handlePasswordLogin(e)
            }}
            className="space-y-4"
          >
            <div>
              <label htmlFor="login-email" className="mb-1 block text-sm font-medium">
                Email
              </label>
              <Input
                id="login-email"
                type="email"
                required
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value)
                }}
                autoComplete="email"
              />
            </div>
            <div>
              <label htmlFor="login-password" className="mb-1 block text-sm font-medium">
                Password
              </label>
              <Input
                id="login-password"
                type="password"
                required
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value)
                }}
                autoComplete="current-password"
              />
            </div>
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? 'Signing in...' : 'Sign in'}
            </Button>
          </form>
        ) : (
          <form
            onSubmit={(e) => {
              void handlePasskeyLogin(e)
            }}
            className="space-y-4"
          >
            <div>
              <label htmlFor="passkey-email" className="mb-1 block text-sm font-medium">
                Email
              </label>
              <Input
                id="passkey-email"
                type="email"
                required
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value)
                }}
                autoComplete="email"
              />
            </div>
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? 'Authenticating...' : 'Login with Passkey'}
            </Button>
          </form>
        )}

        <div className="mt-4 text-center text-sm">
          <button
            type="button"
            className="text-primary underline-offset-4 hover:underline"
            onClick={() => {
              setMode(mode === 'password' ? 'passkey' : 'password')
            }}
          >
            {mode === 'password' ? 'Use passkey instead' : 'Use password instead'}
          </button>
        </div>

        <p className="text-muted-foreground mt-4 text-center text-sm">
          Don&apos;t have an account?{' '}
          <Link to="/register" className="text-primary underline-offset-4 hover:underline">
            Register
          </Link>
        </p>
      </CardContent>
    </Card>
  )
}
