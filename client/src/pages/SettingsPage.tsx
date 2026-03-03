// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useEffect, useState } from 'react'

import { PasskeyManager } from '@/components/auth/PasskeyManager'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const SESSION_SIZE_KEY = 'sessionSize'
const DARK_MODE_KEY = 'darkMode'
const DEFAULT_SESSION_SIZE = 20

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

export function SettingsPage() {
  const [sessionSize, setSessionSize] = useState<number>(() => {
    const stored = localStorage.getItem(SESSION_SIZE_KEY)
    return stored ? clamp(parseInt(stored, 10), 5, 100) : DEFAULT_SESSION_SIZE
  })

  const [darkMode, setDarkMode] = useState<boolean>(() => {
    const stored = localStorage.getItem(DARK_MODE_KEY)
    if (stored !== null) return stored === 'true'
    return document.documentElement.classList.contains('dark')
  })

  useEffect(() => {
    localStorage.setItem(SESSION_SIZE_KEY, String(sessionSize))
  }, [sessionSize])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
    localStorage.setItem(DARK_MODE_KEY, String(darkMode))
  }, [darkMode])

  function toggleDarkMode() {
    setDarkMode((prev) => !prev)
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      {/* Session size */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Session size</CardTitle>
          <p className="text-muted-foreground text-sm">
            Number of concepts per study session (5–100).
          </p>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <input
              type="range"
              min={5}
              max={100}
              step={5}
              value={sessionSize}
              onChange={(e) => setSessionSize(Number(e.target.value))}
              className="w-48"
              aria-label="Session size"
            />
            <span className="w-8 text-center font-medium">{sessionSize}</span>
          </div>
        </CardContent>
      </Card>

      {/* Theme */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Theme</CardTitle>
        </CardHeader>
        <CardContent>
          <Button variant="outline" aria-pressed={darkMode} onClick={toggleDarkMode}>
            {darkMode ? 'Switch to Light mode' : 'Switch to Dark mode'}
          </Button>
        </CardContent>
      </Card>

      {/* Account / Passkeys */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Passkeys</CardTitle>
          <p className="text-muted-foreground text-sm">
            Manage your passwordless sign-in methods.
          </p>
        </CardHeader>
        <CardContent>
          <PasskeyManager />
        </CardContent>
      </Card>
    </div>
  )
}
