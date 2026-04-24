import client from './client'
import type { LoginResponse, User } from '../types/auth'

// Backend expects JSON body {email, password} — NOT form-encoded
export async function login(email: string, password: string): Promise<LoginResponse> {
  const res = await client.post<LoginResponse>('/api/v1/auth/login', { email, password })
  return res.data
}

// Backend uses full_name field, not display_name
export async function register(email: string, password: string, full_name: string) {
  const res = await client.post('/api/v1/auth/register', { email, password, full_name })
  return res.data
}

export async function refreshToken(): Promise<LoginResponse> {
  // Send null body — {} causes FastAPI 422 because RefreshRequest.refresh_token is required
  // With null, FastAPI treats body as None (RefreshRequest | None = None) and reads the httpOnly cookie
  const res = await client.post<LoginResponse>('/api/v1/auth/refresh', null, { withCredentials: true })
  return res.data
}

export async function logout() {
  await client.post('/api/v1/auth/logout').catch(() => {})
}

export async function getMe(): Promise<User> {
  const res = await client.get<User>('/api/v1/auth/me')
  return res.data
}

// Backend uses POST with JSON body {code: string}
export async function verifyEmail(code: string) {
  const res = await client.post('/api/v1/auth/verify-email', { code })
  return res.data
}

export async function forgotPassword(email: string) {
  const res = await client.post('/api/v1/auth/forgot-password', { email })
  return res.data
}

// Backend uses reset_password with body {code, new_password}
export async function resetPassword(code: string, new_password: string) {
  const res = await client.post('/api/v1/auth/reset-password', { code, new_password })
  return res.data
}

export async function changePassword(current_password: string, new_password: string) {
  const res = await client.put('/api/v1/auth/change-password', { current_password, new_password })
  return res.data
}
