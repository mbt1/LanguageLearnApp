// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import { useAuth } from '@/auth/AuthContext'
import { VerifyEmailBanner } from '@/components/auth/VerifyEmailBanner'
import { PasskeyManager } from '@/components/auth/PasskeyManager'
import { Button } from '@/components/ui/button'

export function DashboardPage() {
  const { user, logout } = useAuth()

  return (
    <main className="mx-auto max-w-2xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">LanguageLearn</h1>
        <Button variant="outline" onClick={() => void logout()}>
          Logout
        </Button>
      </div>

      {user && !user.email_verified && <VerifyEmailBanner />}

      <p className="text-muted-foreground">
        Welcome, {user?.email}. Learning features coming soon!
      </p>

      <PasskeyManager />
    </main>
  )
}
