import client from './client'
import type { FusionResponse, LLMAnalysis } from '../types/fusion'

export async function getFusion(symbol: string): Promise<FusionResponse> {
  const res = await client.get<FusionResponse>(`/api/v1/fusion/${encodeURIComponent(symbol)}`)
  return res.data
}

export async function getLLMAnalysis(symbol: string): Promise<LLMAnalysis> {
  // POST /{symbol}/llm-analysis with FusionRequest body
  const res = await client.post<LLMAnalysis>(
    `/api/v1/fusion/${encodeURIComponent(symbol)}/llm-analysis`,
    {
      symbol: symbol,
      include_sentiment: true,
      include_llm: true,
    }
  )
  return res.data
}
