import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import type { User } from '../types/auth'
import * as authApi from '../api/auth'
import { setToken } from '../api/client'

interface AuthContextValue {
  user: User | null
  token: string | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  setUser: (user: User | null) => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setTokenState] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // On mount — try silent refresh via httpOnly cookie
  useEffect(() => {
    authApi
      .refreshToken()
      .then(async (data) => {
        setToken(data.access_token)
        setTokenState(data.access_token)
        const me = await authApi.getMe()
        setUser(me)
      })
      .catch(() => {
        // No valid session — that's fine, user needs to log in
      })
      .finally(() => setIsLoading(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const data = await authApi.login(email, password)
    setToken(data.access_token)
    setTokenState(data.access_token)
    const me = await authApi.getMe()
    setUser(me)
  }, [])

  const logout = useCallback(async () => {
    await authApi.logout()
    setToken(null)
    setTokenState(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}
