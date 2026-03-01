// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import * as authApi from '@/api/auth'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const token = useMemo(() => searchParams.get('token'), [searchParams])

  const initialStatus = token ? 'loading' : 'error'
  const initialMessage = token ? '' : 'No verification token provided'

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>(initialStatus)
  const [message, setMessage] = useState(initialMessage)

  useEffect(() => {
    if (!token) return
    void authApi
      .verifyEmail(token)
      .then((data) => {
        setStatus('success')
        setMessage(data.message)
      })
      .catch(() => {
        setStatus('error')
        setMessage('Verification failed. The link may be expired or invalid.')
      })
  }, [token])

  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <Card className="mx-auto w-full max-w-sm">
        <CardHeader>
          <CardTitle>Email Verification</CardTitle>
        </CardHeader>
        <CardContent>
          {status === 'loading' && <p>Verifying...</p>}
          {status === 'success' && (
            <>
              <p className="text-sm text-green-700 dark:text-green-300">{message}</p>
              <Button asChild className="mt-4 w-full">
                <Link to="/login">Go to Login</Link>
              </Button>
            </>
          )}
          {status === 'error' && (
            <>
              <p className="text-destructive text-sm">{message}</p>
              <Button asChild variant="outline" className="mt-4 w-full">
                <Link to="/login">Back to Login</Link>
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </main>
  )
}
