export interface User {
  id: string
  email: string
  full_name: string
  subscription_tier: 'free' | 'pro' | 'admin'
  is_verified: boolean
  is_active: boolean
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
}
