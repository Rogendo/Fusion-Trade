import client from './client'

export interface NewsletterRequest {
  symbols?: string[]
  recipients?: string[]
  include_llm?: boolean
  period?: string
}

export async function getPreview(req: NewsletterRequest = {}): Promise<{ preview_html: string }> {
  const body: NewsletterRequest = {
    symbols: ['EURUSD=X', 'GBPUSD=X', 'GC=F', 'BTC-USD'],
    include_llm: false,   // default off — LLM preview takes 2–3 min per symbol
    period: 'daily',
    ...req,
  }
  // Large timeout: preview without LLM ~30s, with LLM ~3min per symbol
  const timeout = body.include_llm ? 5 * 60 * 1000 : 120 * 1000
  const res = await client.post<{ preview_html: string }>('/api/v1/newsletter/preview', body, { timeout })
  return res.data
}

export async function triggerNewsletter(req: NewsletterRequest = {}) {
  const body: NewsletterRequest = {
    symbols: ['EURUSD=X', 'GBPUSD=X', 'GC=F', 'BTC-USD'],
    include_llm: false,
    period: 'daily',
    ...req,
  }
  // Trigger runs async in background — 30s timeout for acknowledgement
  const res = await client.post('/api/v1/newsletter/trigger', body, { timeout: 30_000 })
  return res.data
}
