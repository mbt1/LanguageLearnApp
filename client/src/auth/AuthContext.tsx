// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 LanguageLearn Contributors

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import type { AuthUser } from '@/api/auth'
import * as authApi from '@/api/auth'

/* ── Context shape ─────────────────────────────────────────── */

interface AuthContextValue {
  user: AuthUser | null
  isLoading: boolean
  register: (email: string, password: string, displayName?: string) => Promise<void>
  login: (email: string, password: string) => Promise<void>
  loginWithPasskey: (email: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

/* ── Provider ──────────────────────────────────────────────── */

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Attempt silent refresh on mount
  useEffect(() => {
    let cancelled = false
    void authApi.refreshToken().then((u) => {
      if (!cancelled) {
        setUser(u)
        setIsLoading(false)
      }
    })
    return () => {
      cancelled = true
    }
  }, [])

  const register = useCallback(async (email: string, password: string, displayName?: string) => {
    const u = await authApi.register(email, password, displayName)
    setUser(u)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const u = await authApi.login(email, password)
    setUser(u)
  }, [])

  const loginWithPasskey = useCallback(async (email: string) => {
    const { startAuthentication } = await import('@simplewebauthn/browser')
    const optionsJSON = await authApi.getPasskeyAuthenticationOptions(email)
    const options = JSON.parse(optionsJSON) as Parameters<
      typeof startAuthentication
    >[0]['optionsJSON']
    const credential = await startAuthentication({ optionsJSON: options })
    const u = await authApi.verifyPasskeyAuthentication(email, JSON.stringify(credential))
    setUser(u)
  }, [])

  const logout = useCallback(async () => {
    await authApi.logout()
    setUser(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({ user, isLoading, register, login, loginWithPasskey, logout }),
    [user, isLoading, register, login, loginWithPasskey, logout],
  )

  return <AuthContext value={value}>{children}</AuthContext>
}
