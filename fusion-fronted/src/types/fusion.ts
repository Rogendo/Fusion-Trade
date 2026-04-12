export interface Headline {
  title: string
  source: string
  summary: string
  published: string
  link: string
}

export interface SentimentBlock {
  overall_score: number           // -1.0 to +1.0
  overall_sentiment: string       // "Bullish", "Bearish", etc
  trading_bias: string
  bias_strength: string
  positive_count: number
  negative_count: number
  neutral_count: number
  news_count: number
  top_headlines: Headline[]
}

export interface TimeframeSignal {
  lstm: 'BUY' | 'SELL' | 'HOLD' | null
  patchtst: 'BUY' | 'SELL' | 'HOLD' | null
  agreement: number               // 0.0–1.0
  lstm_confidence: number
  lstm_direction_confidence: number
  lstm_direction_accuracy: number | null
  patchtst_confidence: number
  patchtst_prob_up: number
  patchtst_prob_flat: number
  patchtst_prob_down: number
  current_price: number
  predicted_price: number
}

export interface Targets {
  tp1: number | null
  tp2: number | null
  tp3: number | null
  sl: number | null
  atr: number | null
}

export interface FusionLogic {
  primary_lstm?: string
  secondary_patchtst?: string
  confluence?: boolean
  [key: string]: unknown
}

export interface FusionResponse {
  symbol: string
  master_fusion_score: number     // 0–100
  verdict: string                 // e.g. "DIVERGENT (HOLD)", "HIGH CONVICTION (BUY)"
  logic: FusionLogic | string | null
  reasoning: string
  timeframes: Record<string, TimeframeSignal>   // dict keyed by interval
  targets: Targets
  sentiment: SentimentBlock | null
  llm_analysis: LLMAnalysis | null
}

export interface KeyLevels {
  tp1: number
  sl: number
}

export interface LLMAnalysis {
  action: 'BUY' | 'SELL' | 'WAIT' | 'HOLD'
  confidence_level: 'high' | 'medium' | 'low'   // NOT confidence
  independent_bias: string
  validates_fusion: boolean
  divergence_reason: string | null
  market_structure: string
  news_impact: string
  entry_strategy: string
  key_levels: Record<string, number>             // flexible dict from backend
  warnings: string[]                             // NOT risk_warnings
  raw_response: string
}
