import client from './client'
import type { JournalResponse } from '../types/journal'

export async function getJournal(
  page = 1,
  page_size = 50,
  symbol?: string,
  status?: string,
): Promise<JournalResponse> {
  const res = await client.get<JournalResponse>('/api/v1/journal/', {
    params: { page, page_size, symbol, status },
  })
  return res.data
}

export async function triggerVerification(): Promise<{ status: string; result?: { verified: number } }> {
  const res = await client.post('/api/v1/journal/verify-now')
  return res.data
}
