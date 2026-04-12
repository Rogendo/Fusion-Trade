import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { BarChart2, BookOpen, Cpu, Mail, Settings, LogOut, Zap, Info } from 'lucide-react'
import { SYMBOL_GROUPS, getLabel } from '../../utils/symbolMeta'
import { MarketSessions } from './MarketSessions'

const navLinks = [
  { to: '/journal',    label: 'Journal',    icon: BookOpen },
  { to: '/models',     label: 'Models',     icon: Cpu },
  { to: '/newsletter', label: 'Newsletter', icon: Mail },
  { to: '/about',      label: 'About',      icon: Info },
  { to: '/settings',   label: 'Settings',   icon: Settings },
]

export function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <aside className="hidden lg:flex flex-col w-56 bg-terminal-surface border-r border-terminal-border h-screen sticky top-0 shrink-0">
      {/* Logo */}
      <div className="p-4 border-b border-terminal-border shrink-0">
        <div className="flex items-center gap-2">
          <Zap className="h-5 w-5 text-emerald-400" />
          <span className="font-bold text-slate-200 text-sm">FusionTrade AI</span>
        </div>
      </div>

      {/* Market sessions */}
      <MarketSessions />

      {/* Markets + nav — scrollable */}
      <div className="flex-1 overflow-y-auto py-2">
        {SYMBOL_GROUPS.map(group => (
          <div key={group.group} className="px-3 mb-3">
            <p className="text-[9px] text-slate-700 uppercase tracking-wider mb-1 px-1">
              {group.group}
            </p>
            <div className="space-y-0.5">
              {group.symbols.map(sym => (
                <NavLink
                  key={sym}
                  to={`/analysis/${encodeURIComponent(sym)}`}
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs transition-colors ${
                      isActive
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : 'text-slate-400 hover:bg-terminal-muted hover:text-slate-200'
                    }`
                  }
                >
                  <BarChart2 className="h-3 w-3 shrink-0" />
                  <span className="truncate">{getLabel(sym)}</span>
                </NavLink>
              ))}
            </div>
          </div>
        ))}

        {/* Nav links */}
        <div className="border-t border-terminal-border mx-3 my-2" />
        <nav className="px-3 space-y-0.5">
          {navLinks.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs transition-colors ${
                  isActive
                    ? 'bg-terminal-muted text-slate-200'
                    : 'text-slate-500 hover:bg-terminal-muted hover:text-slate-200'
                }`
              }
            >
              <Icon className="h-3.5 w-3.5 shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* User */}
      {user && (
        <div className="p-3 border-t border-terminal-border shrink-0">
          <div className="px-2 py-1.5">
            <p className="text-xs font-medium text-slate-300 truncate">{user.full_name}</p>
            <p className="text-[10px] text-slate-600 truncate">{user.email}</p>
            <span className={`text-[10px] px-1.5 py-0.5 rounded mt-1 inline-block ${
              user.subscription_tier !== 'free'
                ? 'bg-emerald-500/20 text-emerald-400'
                : 'bg-slate-500/20 text-slate-400'
            }`}>
              {user.subscription_tier.toUpperCase()}
            </span>
          </div>
          <button
            onClick={async () => { await logout(); navigate('/login') }}
            className="flex items-center gap-2 px-2.5 py-1.5 w-full text-xs text-slate-600 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors mt-1"
          >
            <LogOut className="h-3.5 w-3.5" />
            Sign out
          </button>
        </div>
      )}
    </aside>
  )
}
