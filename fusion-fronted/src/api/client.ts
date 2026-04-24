import axios from 'axios'

const client = axios.create({
  baseURL: '',
  withCredentials: true,  // send httpOnly refresh_token cookie
})

// Inject access token from in-memory store
let _token: string | null = null

export function setToken(token: string | null) {
  _token = token
}

export function getToken() {
  return _token
}

client.interceptors.request.use((config) => {
  if (_token) {
    config.headers.Authorization = `Bearer ${_token}`
  }
  return config
})

// Track refresh state to prevent loops
let _refreshing = false
let _refreshSubscribers: Array<(token: string | null) => void> = []

function subscribeRefresh(cb: (token: string | null) => void) {
  _refreshSubscribers.push(cb)
}

function notifyRefreshSubscribers(token: string | null) {
  _refreshSubscribers.forEach((cb) => cb(token))
  _refreshSubscribers = []
}

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config

    // Never retry auth endpoints — would cause infinite reload loop on /login
    const url: string = original.url ?? ''
    const isAuthEndpoint = url.includes('/auth/')

    if (error.response?.status === 401 && !original._retry && !isAuthEndpoint) {
      original._retry = true

      if (_refreshing) {
        return new Promise((resolve, reject) => {
          subscribeRefresh((newToken) => {
            if (newToken) {
              original.headers.Authorization = `Bearer ${newToken}`
              resolve(client(original))
            } else {
              reject(error)
            }
          })
        })
      }

      _refreshing = true
      try {
        const res = await axios.post(
          '/api/v1/auth/refresh',
          null,   // null body — {} causes FastAPI 422 on RefreshRequest validation
          { withCredentials: true }
        )
        const newToken: string = res.data.access_token
        setToken(newToken)
        notifyRefreshSubscribers(newToken)
        original.headers.Authorization = `Bearer ${newToken}`
        return client(original)
      } catch {
        setToken(null)
        notifyRefreshSubscribers(null)
        window.location.href = '/login'
        return Promise.reject(error)
      } finally {
        _refreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export default client
