import { useQuery } from '@tanstack/react-query'
import { getFusion } from '../api/fusion'

export function useFusion(symbol: string) {
  return useQuery({
    queryKey: ['fusion', symbol],
    queryFn: () => getFusion(symbol),
    refetchInterval: 3 * 60 * 1000,  // 3 minutes
    staleTime: 60 * 1000,
    retry: 2,
  })
}
