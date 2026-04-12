import { useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { resetPassword } from '../../api/auth'
import { Button } from '../../components/ui/Button'

export function ResetPasswordPage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const token = params.get('token')
    if (!token) { setError('Invalid link.'); return }
    setLoading(true)
    try {
      await resetPassword(token, password)
      navigate('/login')
    } catch {
      setError('Reset failed. Link may be expired.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-terminal-bg flex items-center justify-center p-4">
      <div className="w-full max-w-sm space-y-6">
        <h1 className="text-center text-xl font-semibold text-slate-200">New password</h1>
        <form onSubmit={handleSubmit} className="bg-terminal-surface border border-terminal-border rounded-xl p-6 space-y-4">
          {error && <p className="text-xs text-rose-400">{error}</p>}
          <div className="space-y-2">
            <label className="text-xs text-slate-400">New password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              minLength={8}
              className="w-full bg-terminal-bg border border-terminal-border rounded-lg px-3 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
              placeholder="••••••••"
            />
          </div>
          <Button type="submit" loading={loading} className="w-full justify-center">
            Set password
          </Button>
        </form>
      </div>
    </div>
  )
}
