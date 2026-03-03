// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '@/auth/AuthContext'
import { VerifyEmailBanner } from '@/components/auth/VerifyEmailBanner'
import { Button } from '@/components/ui/button'

export function NavShell() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="mx-auto flex max-w-4xl items-center gap-6 px-4 py-3">
          <NavLink to="/" className="text-lg font-bold tracking-tight">
            LanguageLearn
          </NavLink>
          <nav className="flex items-center gap-4 text-sm">
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
              to="/progress"
              className={({ isActive }) =>
                isActive ? 'font-medium text-foreground' : 'text-muted-foreground hover:text-foreground'
              }
            >
              Progress
            </NavLink>
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                isActive ? 'font-medium text-foreground' : 'text-muted-foreground hover:text-foreground'
              }
            >
              Settings
            </NavLink>
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
