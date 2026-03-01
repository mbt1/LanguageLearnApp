// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useState } from 'react'

import * as authApi from '@/api/auth'
import { Button } from '@/components/ui/button'
import { ApiError } from '@/api/client'

export function VerifyEmailBanner() {
  const [sent, setSent] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSending, setIsSending] = useState(false)

  async function handleResend() {
    setError(null)
    setIsSending(true)
    try {
      await authApi.resendVerification()
      setSent(true)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail)
      } else {
        setError('Failed to resend')
      }
    } finally {
      setIsSending(false)
    }
  }

  return (
    <div className="rounded-md border border-yellow-300 bg-yellow-50 p-4 text-sm text-yellow-800 dark:border-yellow-700 dark:bg-yellow-950 dark:text-yellow-200">
      <p className="font-medium">Email not verified</p>
      <p className="mt-1">Please check your inbox for a verification link.</p>
      {error && <p className="text-destructive mt-1">{error}</p>}
      {sent ? (
        <p className="mt-2 font-medium">Verification email sent!</p>
      ) : (
        <Button
          variant="outline"
          size="sm"
          className="mt-2"
          disabled={isSending}
          onClick={() => {
            void handleResend()
          }}
        >
          {isSending ? 'Sending...' : 'Resend verification email'}
        </Button>
      )}
    </div>
  )
}
