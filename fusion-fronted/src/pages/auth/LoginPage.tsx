import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { Button } from '../../components/ui/Button'
import { Zap } from 'lucide-react'
import axios from 'axios'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/analysis/GC%3DF', { replace: true })
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail
        // FastAPI 422 returns detail as array of {type, loc, msg, input}
        const msg = Array.isArray(detail)
          ? detail.map((d: any) => d.msg).join(', ')
          : typeof detail === 'string'
          ? detail
          : 'Login failed. Check your credentials.'
        setError(msg)
      } else {
        setError('An unexpected error occurred.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-terminal-bg flex items-center justify-center p-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="flex flex-col items-center gap-3">
          <div className="flex items-center gap-2">
            <Zap className="h-6 w-6 text-emerald-400" />
            <span className="text-xl font-bold text-slate-200">FusionTrade AI</span>
          </div>
          <p className="text-sm text-slate-400">Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-terminal-surface border border-terminal-border rounded-xl p-6 space-y-4">
          {error && (
            <p className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
              {error}
            </p>
          )}
          <div className="space-y-2">
            <label className="text-xs text-slate-400">Email</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              className="w-full bg-terminal-bg border border-terminal-border rounded-lg px-3 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
              placeholder="you@example.com"
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs text-slate-400">Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              className="w-full bg-terminal-bg border border-terminal-border rounded-lg px-3 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
              placeholder="••••••••"
            />
          </div>
          <div className="flex justify-end">
            <Link to="/forgot-password" className="text-xs text-slate-500 hover:text-slate-300">
              Forgot password?
            </Link>
          </div>
          <Button type="submit" loading={loading} className="w-full justify-center">
            Sign In
          </Button>
        </form>

        <p className="text-center text-xs text-slate-500">
          Don't have an account?{' '}
          <Link to="/register" className="text-emerald-400 hover:text-emerald-300">
            Register
          </Link>
        </p>
      </div>
    </div>
  )
}
