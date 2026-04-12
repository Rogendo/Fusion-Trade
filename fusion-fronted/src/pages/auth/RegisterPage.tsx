import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../../api/auth'
import { Button } from '../../components/ui/Button'
import { Zap } from 'lucide-react'
import axios from 'axios'

export function RegisterPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '', full_name: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(form.email, form.password, form.full_name)
      setDone(true)
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail
        const msg = Array.isArray(detail)
          ? detail.map((d: any) => d.msg).join(', ')
          : typeof detail === 'string'
          ? detail
          : 'Registration failed.'
        setError(msg)
      } else {
        setError('An unexpected error occurred.')
      }
    } finally {
      setLoading(false)
    }
  }

  if (done) {
    return (
      <div className="min-h-screen bg-terminal-bg flex items-center justify-center p-4">
        <div className="bg-terminal-surface border border-emerald-500/30 rounded-xl p-8 text-center max-w-sm space-y-4">
          <Zap className="h-8 w-8 text-emerald-400 mx-auto" />
          <h2 className="text-lg font-semibold text-slate-200">Check your email</h2>
          <p className="text-sm text-slate-400">
            We've sent a verification link to <strong>{form.email}</strong>.
            Click it to activate your account.
          </p>
          <Button variant="ghost" onClick={() => navigate('/login')}>Back to login</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-terminal-bg flex items-center justify-center p-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="flex flex-col items-center gap-3">
          <div className="flex items-center gap-2">
            <Zap className="h-6 w-6 text-emerald-400" />
            <span className="text-xl font-bold text-slate-200">FusionTrade AI</span>
          </div>
          <p className="text-sm text-slate-400">Create your account</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-terminal-surface border border-terminal-border rounded-xl p-6 space-y-4">
          {error && (
            <p className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
              {error}
            </p>
          )}
          {[
            { key: 'full_name', label: 'Full Name', type: 'text', placeholder: 'Your name' },
            { key: 'email', label: 'Email', type: 'email', placeholder: 'you@example.com' },
            { key: 'password', label: 'Password', type: 'password', placeholder: '••••••••' },
          ].map(({ key, label, type, placeholder }) => (
            <div key={key} className="space-y-2">
              <label className="text-xs text-slate-400">{label}</label>
              <input
                type={type}
                value={form[key as keyof typeof form]}
                onChange={set(key)}
                required
                className="w-full bg-terminal-bg border border-terminal-border rounded-lg px-3 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
                placeholder={placeholder}
              />
            </div>
          ))}
          <Button type="submit" loading={loading} className="w-full justify-center">
            Create Account
          </Button>
        </form>

        <p className="text-center text-xs text-slate-500">
          Already have an account?{' '}
          <Link to="/login" className="text-emerald-400 hover:text-emerald-300">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
