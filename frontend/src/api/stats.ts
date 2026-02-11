import { useQuery } from '@tanstack/react-query'
import { apiGet } from './client'
import type { Stats } from '../types'

export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: () => apiGet<Stats>('/stats/'),
  })
}
