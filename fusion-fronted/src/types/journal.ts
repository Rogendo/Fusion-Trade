export type JournalStatus = 'PENDING' | 'TP1_HIT' | 'TP2_HIT' | 'TP3_HIT' | 'SL_HIT' | 'EXPIRED' | 'IGNORED'
export type JournalOutcome = 'WIN' | 'LOSS' | 'NEUTRAL' | null

export interface JournalEntry {
  id: string
  symbol: string
  interval: string
  signal: string
  lstm_signal: string | null
  patchtst_signal: string | null
  fusion_score: number | null
  entry_price: number | null
  take_profit_1: number | null
  take_profit_2: number | null
  take_profit_3: number | null
  stop_loss: number | null
  confidence: number | null
  status: JournalStatus
  outcome: JournalOutcome
  exit_price: number | null
  pips: number | null
  created_at: string
  verified_at: string | null
}

export interface JournalStats {
  total_trades: number
  wins: number
  losses: number
  pending: number
  win_rate: number        // 0–100
  profit_factor: number
  total_pips: number
  max_drawdown: number
}

export interface JournalResponse {
  entries: JournalEntry[]
  stats: JournalStats
  page: number
  page_size: number
  total: number
}
