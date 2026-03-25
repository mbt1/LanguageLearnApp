// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '@/auth/AuthContext'
import { VerifyEmailBanner } from '@/components/auth/VerifyEmailBanner'
import { Button } from '@/components/ui/button'

export function NavShell() {
  const { user, logout } = useAuth()
  const [showReviewSchedule, setShowReviewSchedule] = useState(
    () => localStorage.getItem('showReviewSchedule') === 'true',
  )

  useEffect(() => {
    function onSettingsChange() {
      setShowReviewSchedule(localStorage.getItem('showReviewSchedule') === 'true')
    }
    window.addEventListener('settings-changed', onSettingsChange)
    return () => { window.removeEventListener('settings-changed', onSettingsChange); }
  }, [])

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="mx-auto flex max-w-4xl flex-wrap items-center gap-4 px-4 py-3">
          <NavLink to="/" className="text-lg font-bold tracking-tight">
            LanguageLearn
          </NavLink>
          <nav aria-label="Main navigation" className="flex items-center gap-4 text-sm">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                isActive ? 'font-medium text-foreground' : 'text-muted-foreground hover:text-foreground'
              }
            >
              Courses
            </NavLink>
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                isActive ? 'font-medium text-foreground' : 'text-muted-foreground hover:text-foreground'
              }
            >
              Settings
            </NavLink>
            {showReviewSchedule && (
              <NavLink
                to="/review-schedule"
                className={({ isActive }) =>
                  isActive ? 'font-medium text-foreground' : 'text-muted-foreground hover:text-foreground'
                }
              >
                Schedule
              </NavLink>
            )}
          </nav>
          <div className="ml-auto">
            <Button variant="outline" size="sm" onClick={() => void logout()}>
              Logout
            </Button>
          </div>
        </div>
      </header>

      {user && !user.email_verified && (
        <div className="mx-auto max-w-4xl px-4 pt-4">
          <VerifyEmailBanner />
        </div>
      )}

      <main className="mx-auto max-w-4xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
