import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPatch } from './client'
import type { Job, JobListResponse, JobFilters } from '../types'

export function useJobs(filters: JobFilters) {
  return useQuery({
    queryKey: ['jobs', filters],
    queryFn: () => apiGet<JobListResponse>('/jobs/', filters as Record<string, string | number | undefined>),
  })
}

export function useJob(id: string) {
  return useQuery({
    queryKey: ['job', id],
    queryFn: () => apiGet<Job>(`/jobs/${id}`),
    enabled: !!id,
  })
}

export function useUpdateJobStatus() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status, notes }: { id: string; status: string; notes?: string }) =>
      apiPatch<{ id: string; status: string }>(`/jobs/${id}/status`, { status, notes }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['jobs'] })
      qc.invalidateQueries({ queryKey: ['job'] })
      qc.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}
