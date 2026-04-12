import { useQuery } from '@tanstack/react-query'
import { getJournal } from '../api/journal'

export function useJournal(page = 1) {
  return useQuery({
    queryKey: ['journal', page],
    queryFn: () => getJournal(page, 20),
    staleTime: 30 * 1000,
  })
}
