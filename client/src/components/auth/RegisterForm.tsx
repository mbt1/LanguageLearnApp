// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { ApiError } from '@/api/client'

export function RegisterForm() {
  const { register } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(e: React.SyntheticEvent) {
    e.preventDefault()
    setError(null)

    if (password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    setIsSubmitting(true)
    try {
      await register(email, password, displayName || undefined)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail)
      } else {
        setError('Registration failed')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Card className="mx-auto w-full max-w-sm">
      <CardHeader>
        <CardTitle>Create Account</CardTitle>
        <CardDescription>Get started with LanguageLearn</CardDescription>
      </CardHeader>
      <CardContent>
        {error && (
          <p className="text-destructive mb-4 text-sm" role="alert">
            {error}
          </p>
        )}

        <form
          onSubmit={(e) => {
            void handleSubmit(e)
          }}
          className="space-y-4"
        >
          <div>
            <label htmlFor="reg-email" className="mb-1 block text-sm font-medium">
              Email
            </label>
            <Input
              id="reg-email"
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
            <label htmlFor="reg-display-name" className="mb-1 block text-sm font-medium">
              Display Name (optional)
            </label>
            <Input
              id="reg-display-name"
              type="text"
              value={displayName}
              onChange={(e) => {
                setDisplayName(e.target.value)
              }}
              autoComplete="name"
            />
          </div>
          <div>
            <label htmlFor="reg-password" className="mb-1 block text-sm font-medium">
              Password
            </label>
            <Input
              id="reg-password"
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => {
                setPassword(e.target.value)
              }}
              autoComplete="new-password"
            />
          </div>
          <div>
            <label htmlFor="reg-confirm-password" className="mb-1 block text-sm font-medium">
              Confirm Password
            </label>
            <Input
              id="reg-confirm-password"
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value)
              }}
              autoComplete="new-password"
            />
          </div>
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? 'Creating account...' : 'Create account'}
          </Button>
        </form>

        <p className="text-muted-foreground mt-4 text-center text-sm">
          Already have an account?{' '}
          <Link to="/login" className="text-primary underline-offset-4 hover:underline">
            Login
          </Link>
        </p>
      </CardContent>
    </Card>
  )
}
