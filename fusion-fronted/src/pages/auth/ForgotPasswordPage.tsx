import { useState } from 'react'
import { Link } from 'react-router-dom'
import { forgotPassword } from '../../api/auth'
import { Button } from '../../components/ui/Button'

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [done, setDone] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    await forgotPassword(email).catch(() => {})
    setDone(true)
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-terminal-bg flex items-center justify-center p-4">
      <div className="w-full max-w-sm space-y-6">
        <h1 className="text-center text-xl font-semibold text-slate-200">Reset password</h1>
        {done ? (
          <div className="bg-terminal-surface border border-emerald-500/30 rounded-xl p-6 text-sm text-slate-300 text-center space-y-2">
            <p>If that email is registered, you'll receive a reset link shortly.</p>
            <Link to="/login" className="text-emerald-400 hover:text-emerald-300">Back to login</Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="bg-terminal-surface border border-terminal-border rounded-xl p-6 space-y-4">
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
            <Button type="submit" loading={loading} className="w-full justify-center">
              Send reset link
            </Button>
            <p className="text-center text-xs text-slate-500">
              <Link to="/login" className="text-slate-400 hover:text-slate-200">Back to login</Link>
            </p>
          </form>
        )}
      </div>
    </div>
  )
}
