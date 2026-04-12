import { useState, useEffect } from 'react'
import { Clock } from 'lucide-react'

interface Session {
  name: string
  short: string
  openUTC: number   // hour (0–23)
  closeUTC: number  // hour (0–23), can be < open if crosses midnight
  color: string
  activeBg: string
  activeBorder: string
}

const SESSIONS: Session[] = [
  {
    name: 'Sydney',
    short: 'SYD',
    openUTC: 22,
    closeUTC: 7,     // crosses midnight
    color: 'text-sky-400',
    activeBg: 'bg-sky-500/20',
    activeBorder: 'border-sky-500/40',
  },
  {
    name: 'Tokyo',
    short: 'TYO',
    openUTC: 0,
    closeUTC: 9,
    color: 'text-violet-400',
    activeBg: 'bg-violet-500/20',
    activeBorder: 'border-violet-500/40',
  },
  {
    name: 'London',
    short: 'LON',
    openUTC: 8,
    closeUTC: 17,
    color: 'text-amber-400',
    activeBg: 'bg-amber-500/20',
    activeBorder: 'border-amber-500/40',
  },
  {
    name: 'New York',
    short: 'NY',
    openUTC: 13,
    closeUTC: 22,
    color: 'text-emerald-400',
    activeBg: 'bg-emerald-500/20',
    activeBorder: 'border-emerald-500/40',
  },
]

function isSessionOpen(session: Session, utcHour: number, utcMinute: number): boolean {
  const t = utcHour + utcMinute / 60
  if (session.openUTC < session.closeUTC) {
    return t >= session.openUTC && t < session.closeUTC
  }
  // Crosses midnight (e.g. Sydney 22:00–07:00)
  return t >= session.openUTC || t < session.closeUTC
}

function formatUTC(): string {
  const now = new Date()
  const h = now.getUTCHours().toString().padStart(2, '0')
  const m = now.getUTCMinutes().toString().padStart(2, '0')
  return `${h}:${m} UTC`
}

export function MarketSessions() {
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 30_000)  // update every 30s
    return () => clearInterval(id)
  }, [])

  const utcHour = now.getUTCHours()
  const utcMin  = now.getUTCMinutes()

  const openSessions = SESSIONS.filter(s => isSessionOpen(s, utcHour, utcMin))
  const isWeekend = now.getUTCDay() === 0 || now.getUTCDay() === 6
  const isMarketOpen = !isWeekend && openSessions.length > 0

  // London/NY overlap = highest liquidity
  const isLondonNYOverlap =
    !isWeekend &&
    isSessionOpen(SESSIONS[2], utcHour, utcMin) &&
    isSessionOpen(SESSIONS[3], utcHour, utcMin)

  return (
    <div className="px-3 py-2.5 border-b border-terminal-border">
      {/* UTC clock + market status */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          <Clock className="h-3 w-3 text-slate-500" />
          <span className="text-[10px] text-slate-500 font-mono">{formatUTC()}</span>
        </div>
        {isWeekend ? (
          <span className="text-[9px] text-slate-600 bg-terminal-muted px-1.5 py-0.5 rounded">
            WEEKEND
          </span>
        ) : isLondonNYOverlap ? (
          <span className="text-[9px] text-emerald-300 bg-emerald-500/20 border border-emerald-500/30 px-1.5 py-0.5 rounded animate-pulse">
            HIGH LIQUIDITY
          </span>
        ) : isMarketOpen ? (
          <span className="text-[9px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded">
            MARKET OPEN
          </span>
        ) : (
          <span className="text-[9px] text-slate-600 bg-terminal-muted px-1.5 py-0.5 rounded">
            CLOSED
          </span>
        )}
      </div>

      {/* Session pills */}
      <div className="grid grid-cols-2 gap-1">
        {SESSIONS.map(session => {
          const open = !isWeekend && isSessionOpen(session, utcHour, utcMin)
          return (
            <div
              key={session.name}
              title={`${session.name}: ${session.openUTC.toString().padStart(2,'0')}:00–${session.closeUTC.toString().padStart(2,'0')}:00 UTC`}
              className={`flex items-center gap-1.5 px-2 py-1 rounded text-[10px] border transition-colors ${
                open
                  ? `${session.activeBg} ${session.activeBorder} ${session.color} font-medium`
                  : 'bg-transparent border-terminal-border text-slate-700'
              }`}
            >
              <span className={`h-1.5 w-1.5 rounded-full flex-shrink-0 ${open ? session.color.replace('text-', 'bg-') : 'bg-slate-700'}`} />
              <span>{session.short}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
