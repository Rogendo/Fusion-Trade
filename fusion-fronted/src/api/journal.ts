import client from './client'
import type { JournalResponse } from '../types/journal'

export async function getJournal(page = 1, page_size = 20): Promise<JournalResponse> {
  const res = await client.get<JournalResponse>('/api/v1/journal/', {
    params: { page, page_size },
  })
  return res.data
}
