import { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { verifyEmail } from '../../api/auth'
import { CheckCircle, XCircle } from 'lucide-react'

export function VerifyEmailPage() {
  const [params] = useSearchParams()
  const [status, setStatus] = useState<'pending' | 'ok' | 'error'>('pending')

  useEffect(() => {
    // Backend expects POST /verify-email with {code: string}
    // Email link format: /verify-email?code=xxx or /verify-email?token=xxx
    const code = params.get('code') ?? params.get('token')
    if (!code) { setStatus('error'); return }
    verifyEmail(code).then(() => setStatus('ok')).catch(() => setStatus('error'))
  }, [])

  return (
    <div className="min-h-screen bg-terminal-bg flex items-center justify-center p-4">
      <div className="bg-terminal-surface border border-terminal-border rounded-xl p-8 text-center max-w-sm space-y-4">
        {status === 'pending' && <p className="text-slate-400 text-sm">Verifying…</p>}
        {status === 'ok' && (
          <>
            <CheckCircle className="h-8 w-8 text-emerald-400 mx-auto" />
            <h2 className="text-lg font-semibold text-slate-200">Email verified!</h2>
            <p className="text-sm text-slate-400">Your account is ready.</p>
            <Link to="/login" className="text-emerald-400 hover:text-emerald-300 text-sm block">Sign in</Link>
          </>
        )}
        {status === 'error' && (
          <>
            <XCircle className="h-8 w-8 text-rose-400 mx-auto" />
            <h2 className="text-lg font-semibold text-slate-200">Verification failed</h2>
            <p className="text-sm text-slate-400">Link may be expired. Try registering again.</p>
            <Link to="/register" className="text-emerald-400 hover:text-emerald-300 text-sm block">Register</Link>
          </>
        )}
      </div>
    </div>
  )
}
