// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useCallback, useEffect, useState } from 'react'

import * as authApi from '@/api/auth'
import type { PasskeyListItem } from '@/api/auth'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ApiError } from '@/api/client'

export function PasskeyManager() {
  const [passkeys, setPasskeys] = useState<PasskeyListItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isAdding, setIsAdding] = useState(false)

  const loadPasskeys = useCallback(async () => {
    try {
      const list = await authApi.listPasskeys()
      setPasskeys(list)
    } catch {
      // Silently fail — user will see empty list
    }
  }, [])

  useEffect(() => {
    void loadPasskeys()
  }, [loadPasskeys])

  async function handleAdd() {
    setError(null)
    setIsAdding(true)
    try {
      const { startRegistration } = await import('@simplewebauthn/browser')
      const optionsJSON = await authApi.getPasskeyRegistrationOptions()
      const options = JSON.parse(optionsJSON) as Parameters<
        typeof startRegistration
      >[0]['optionsJSON']
      const credential = await startRegistration({ optionsJSON: options })
      await authApi.verifyPasskeyRegistration(JSON.stringify(credential), 'My Passkey')
      await loadPasskeys()
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail)
      } else {
        setError('Failed to register passkey')
      }
    } finally {
      setIsAdding(false)
    }
  }

  async function handleDelete(id: string) {
    try {
      await authApi.deletePasskey(id)
      setPasskeys((prev) => prev.filter((pk) => pk.id !== id))
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail)
      } else {
        setError('Failed to remove passkey')
      }
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Passkeys</CardTitle>
      </CardHeader>
      <CardContent>
        {error && (
          <p className="text-destructive mb-4 text-sm" role="alert">
            {error}
          </p>
        )}

        {passkeys.length === 0 ? (
          <p className="text-muted-foreground text-sm">No passkeys registered.</p>
        ) : (
          <ul className="space-y-2">
            {passkeys.map((pk) => (
              <li key={pk.id} className="flex items-center justify-between rounded border p-2">
                <div>
                  <p className="text-sm font-medium">{pk.name}</p>
                  <p className="text-muted-foreground text-xs">
                    Added {new Date(pk.created_at).toLocaleDateString()}
                  </p>
                </div>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => {
                    void handleDelete(pk.id)
                  }}
                >
                  Remove
                </Button>
              </li>
            ))}
          </ul>
        )}

        <Button
          variant="outline"
          className="mt-4"
          disabled={isAdding}
          onClick={() => {
            void handleAdd()
          }}
        >
          {isAdding ? 'Adding...' : 'Add Passkey'}
        </Button>
      </CardContent>
    </Card>
  )
}
