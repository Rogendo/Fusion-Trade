import client from './client'

export async function getModels(model_type?: string) {
  const res = await client.get('/api/v1/ml/registry', {
    params: model_type ? { model_type } : undefined,
  })
  return res.data  // { models: [...] }
}

export async function triggerPredict(symbol: string, interval: string) {
  const res = await client.post('/api/v1/ml/predict/trigger', { symbol, interval })
  return res.data
}

export async function triggerBacktest(symbol: string, interval: string) {
  const res = await client.post('/api/v1/ml/backtest/trigger', { symbol, interval })
  return res.data
}

export async function getModelConfig(): Promise<ModelConfig> {
  const res = await client.get<ModelConfig>('/api/v1/ml/config')
  return res.data
}

export async function updateModelConfig(config: Partial<ModelConfig>): Promise<{ status: string; config: ModelConfig }> {
  const res = await client.put('/api/v1/ml/config', { config })
  return res.data
}

export async function resetModelConfig(): Promise<{ status: string; config: ModelConfig }> {
  const res = await client.post('/api/v1/ml/config/reset')
  return res.data
}

// ── TypeScript shape of model_config.json ──────────────────────────────────

export interface ModelConfig {
  lstm: {
    period_map: Record<string, string>
    confidence_threshold: number
    direction_confidence_threshold: number
  }
  patchtst: {
    min_direction_prob: number
    noise_threshold: number
    strong_signal_threshold: number
    direction_threshold: Record<string, number>
    interval_lookback: Record<string, number>
    interval_patch_len: Record<string, number>
  }
  technical_indicators: {
    rsi_period: number
    macd_fast: number
    macd_slow: number
    macd_signal: number
    atr_period: number
    bb_period: number
    sma_period: number
    roc_period: number
    mom_period: number
  }
  news: {
    fetch_limit: number
    headlines_in_response: number
    headlines_for_llm: number
    sentiment_threshold_bullish: number
    sentiment_threshold_bearish: number
  }
  fusion: {
    agreement_threshold: number
    high_conviction_threshold: number
    moderate_threshold: number
    timeframes: string[]
  }
}
