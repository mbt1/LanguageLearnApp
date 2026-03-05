// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useEffect, useState } from 'react'

import { PasskeyManager } from '@/components/auth/PasskeyManager'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const SESSION_SIZE_KEY = 'sessionSize'
const THEME_KEY = 'theme'
const REVIEW_SCHEDULE_KEY = 'showReviewSchedule'
const DEFAULT_SESSION_SIZE = 20

type Theme = 'auto' | 'light' | 'dark'
const THEMES: Theme[] = ['auto', 'light', 'dark']

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

function resolveTheme(theme: Theme): boolean {
  if (theme === 'dark') return true
  if (theme === 'light') return false
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

export function SettingsPage() {
  const [sessionSize, setSessionSize] = useState<number>(() => {
    const stored = localStorage.getItem(SESSION_SIZE_KEY)
    return stored ? clamp(parseInt(stored, 10), 5, 100) : DEFAULT_SESSION_SIZE
  })

  const [showReviewSchedule, setShowReviewSchedule] = useState<boolean>(
    () => localStorage.getItem(REVIEW_SCHEDULE_KEY) === 'true',
  )

  const [theme, setTheme] = useState<Theme>(() => {
    const stored = localStorage.getItem(THEME_KEY)
    if (stored === 'light' || stored === 'dark') return stored
    // Migrate legacy boolean key
    const legacy = localStorage.getItem('darkMode')
    if (legacy === 'true') return 'dark'
    if (legacy === 'false') return 'light'
    return 'auto'
  })

  useEffect(() => {
    localStorage.setItem(SESSION_SIZE_KEY, String(sessionSize))
  }, [sessionSize])

  useEffect(() => {
    localStorage.setItem(REVIEW_SCHEDULE_KEY, String(showReviewSchedule))
    window.dispatchEvent(new Event('settings-changed'))
  }, [showReviewSchedule])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', resolveTheme(theme))
    localStorage.setItem(THEME_KEY, theme)
    localStorage.removeItem('darkMode')
  }, [theme])

  // When theme is auto, listen for OS preference changes
  useEffect(() => {
    if (theme !== 'auto') return
    const mql = window.matchMedia('(prefers-color-scheme: dark)')
    function onChange() {
      document.documentElement.classList.toggle('dark', mql.matches)
    }
    mql.addEventListener('change', onChange)
    return () => mql.removeEventListener('change', onChange)
  }, [theme])

  function cycleTheme() {
    setTheme((prev) => THEMES[(THEMES.indexOf(prev) + 1) % THEMES.length])
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
          <p className="text-muted-foreground text-sm">
            Auto follows your operating system preference.
          </p>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            {THEMES.map((t) => (
              <Button
                key={t}
                variant={theme === t ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTheme(t)}
                aria-pressed={theme === t}
              >
                {t === 'auto' ? 'Auto' : t === 'light' ? 'Light' : 'Dark'}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Developer tools */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Developer tools</CardTitle>
          <p className="text-muted-foreground text-sm">
            Advanced features for power users.
          </p>
        </CardHeader>
        <CardContent>
          <Button
            variant="outline"
            aria-pressed={showReviewSchedule}
            onClick={() => setShowReviewSchedule((prev) => !prev)}
          >
            {showReviewSchedule ? 'Hide Review Schedule' : 'Show Review Schedule'}
          </Button>
          {showReviewSchedule && (
            <p className="text-muted-foreground mt-2 text-sm">
              The Review Schedule page is now available in the navigation menu.
            </p>
          )}
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
