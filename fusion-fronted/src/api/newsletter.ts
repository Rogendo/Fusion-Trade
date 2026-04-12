import client from './client'

interface NewsletterRequest {
  symbols?: string[]
  include_llm?: boolean
  period?: string
}

export async function getPreview(req: NewsletterRequest = {}): Promise<{ preview_html: string; stats: unknown }> {
  // POST with defaults — all fields optional
  const res = await client.post('/api/v1/newsletter/preview', {
    symbols: req.symbols ?? ['EURUSD=X', 'GBPUSD=X', 'GC=F', 'BTC-USD'],
    include_llm: req.include_llm ?? false,
    period: req.period ?? 'daily',
  })
  return res.data
}

export async function triggerNewsletter() {
  const res = await client.post('/api/v1/newsletter/trigger')
  return res.data
}

export async function sendNewsletter(req: NewsletterRequest = {}) {
  const res = await client.post('/api/v1/newsletter/send', {
    symbols: req.symbols ?? ['EURUSD=X', 'GBPUSD=X', 'GC=F', 'BTC-USD'],
    include_llm: req.include_llm ?? false,
    period: req.period ?? 'daily',
  })
  return res.data
}
