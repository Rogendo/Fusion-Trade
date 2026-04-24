import { useQuery } from '@tanstack/react-query'
import { getJournal } from '../api/journal'

export function useJournal(page = 1, symbol?: string, status?: string) {
  return useQuery({
    queryKey: ['journal', page, symbol, status],
    queryFn: () => getJournal(page, 50, symbol, status),
    staleTime: 30 * 1000,
  })
}
