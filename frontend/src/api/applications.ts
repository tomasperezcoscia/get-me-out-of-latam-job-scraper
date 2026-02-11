import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost, apiPatch } from './client'
import type { Application, ApplicationWithJob, MassApplyStarted, MassApplyProgress } from '../types'

export function useApplications(status?: string) {
  return useQuery({
    queryKey: ['applications', status],
    queryFn: () => apiGet<Application[]>('/applications/', status ? { status } : undefined),
  })
}

export function useApplicationsPipeline() {
  return useQuery({
    queryKey: ['applications-pipeline'],
    queryFn: () => apiGet<ApplicationWithJob[]>('/applications/pipeline'),
  })
}

export function useUpdateApplication() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string; status?: string; notes?: string; interview_notes?: string; follow_up_date?: string }) =>
      apiPatch<Application>(`/applications/${id}`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['applications-pipeline'] })
      qc.invalidateQueries({ queryKey: ['applications'] })
    },
  })
}

export function useCreateApplication() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { job_id: string; cover_letter?: string; resume_version?: string }) =>
      apiPost<Application>('/applications/', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['applications'] })
      qc.invalidateQueries({ queryKey: ['jobs'] })
      qc.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}

export function useApplicationByJob(jobId: string, enabled: boolean) {
  return useQuery({
    queryKey: ['application-by-job', jobId],
    queryFn: () => apiGet<Application>(`/applications/by-job/${jobId}`),
    enabled,
    retry: false,
  })
}

export function useMassApply() {
  return useMutation({
    mutationFn: (jobIds: string[]) =>
      apiPost<MassApplyStarted>('/applications/mass-apply', { job_ids: jobIds }),
  })
}

export function useMassApplyProgress(taskId: string | null) {
  return useQuery({
    queryKey: ['mass-apply-progress', taskId],
    queryFn: () => apiGet<MassApplyProgress>(`/applications/mass-apply/${taskId}`),
    enabled: !!taskId,
    retry: 3,
    retryDelay: 1000,
    refetchInterval: (query) => {
      const data = query.state.data
      if (data && data.done) return false
      // Stop polling if we have persistent errors
      if (query.state.error) return false
      return 2000
    },
  })
}
