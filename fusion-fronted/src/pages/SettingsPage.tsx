import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { changePassword } from '../api/auth'
import { Button } from '../components/ui/Button'
import { Settings, User, Lock } from 'lucide-react'
import toast from 'react-hot-toast'
import axios from 'axios'

export function SettingsPage() {
  const { user, logout } = useAuth()
  const [pwForm, setPwForm] = useState({ current: '', next: '' })
  const [pwLoading, setPwLoading] = useState(false)

  const handlePwChange = async (e: React.FormEvent) => {
    e.preventDefault()
    setPwLoading(true)
    try {
      await changePassword(pwForm.current, pwForm.next)
      toast.success('Password updated.')
      setPwForm({ current: '', next: '' })
    } catch (err) {
      if (axios.isAxiosError(err)) {
        toast.error(err.response?.data?.detail ?? 'Password change failed.')
      } else {
        toast.error('An error occurred.')
      }
    } finally {
      setPwLoading(false)
    }
  }

  return (
    <div className="flex-1 overflow-y-auto">
    <div className="p-6 space-y-6 max-w-lg mx-auto">
      <div className="flex items-center gap-2">
        <Settings className="h-5 w-5 text-slate-400" />
        <h1 className="text-base font-semibold text-slate-200">Settings</h1>
      </div>

      {/* Profile */}
      <div className="bg-terminal-surface border border-terminal-border rounded-xl p-5 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <User className="h-4 w-4 text-slate-400" />
          <h2 className="text-sm font-semibold text-slate-200">Profile</h2>
        </div>
        {user && (
          <div className="space-y-2">
            <div>
              <p className="text-xs text-slate-500 mb-1">Display name</p>
              <p className="text-sm text-slate-200">{user.full_name}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 mb-1">Email</p>
              <p className="text-sm text-slate-200">{user.email}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500 mb-1">Account tier</p>
              <span className={`text-xs px-2 py-0.5 rounded border font-medium ${
                user.subscription_tier !== 'free'
                  ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10'
                  : 'text-slate-400 border-slate-500/30 bg-slate-500/10'
              }`}>
                {user.subscription_tier.toUpperCase()}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Change password */}
      <form onSubmit={handlePwChange} className="bg-terminal-surface border border-terminal-border rounded-xl p-5 space-y-4">
        <div className="flex items-center gap-2">
          <Lock className="h-4 w-4 text-slate-400" />
          <h2 className="text-sm font-semibold text-slate-200">Change Password</h2>
        </div>
        {[
          { key: 'current', label: 'Current password' },
          { key: 'next', label: 'New password' },
        ].map(({ key, label }) => (
          <div key={key} className="space-y-2">
            <label className="text-xs text-slate-400">{label}</label>
            <input
              type="password"
              value={pwForm[key as keyof typeof pwForm]}
              onChange={e => setPwForm(f => ({ ...f, [key]: e.target.value }))}
              required
              minLength={8}
              className="w-full bg-terminal-bg border border-terminal-border rounded-lg px-3 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
              placeholder="••••••••"
            />
          </div>
        ))}
        <Button type="submit" loading={pwLoading} variant="secondary">
          Update password
        </Button>
      </form>

      {/* Danger zone */}
      <div className="bg-terminal-surface border border-rose-500/20 rounded-xl p-5 space-y-3">
        <h2 className="text-sm font-semibold text-rose-400">Sign Out</h2>
        <p className="text-xs text-slate-400">Sign out of all sessions on this device.</p>
        <Button variant="danger" onClick={logout}>
          Sign out
        </Button>
      </div>
    </div>
    </div>
  )
}
