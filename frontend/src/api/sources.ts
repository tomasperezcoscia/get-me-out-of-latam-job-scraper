import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost } from './client'
import type { CollectResult } from '../types'

export function useSources() {
  return useQuery({
    queryKey: ['sources'],
    queryFn: () => apiGet<string[]>('/sources/'),
  })
}

export function useCollectSource() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (source: string) => apiPost<CollectResult>(`/sources/collect/${source}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['jobs'] })
      qc.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}

export function useCollectAll() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => apiPost<CollectResult[]>('/sources/collect-all'),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['jobs'] })
      qc.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}
