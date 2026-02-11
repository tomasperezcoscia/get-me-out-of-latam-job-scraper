import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost, apiPatch } from './client'
import type { ATSResult, LearningItem, SkillSummary } from '../types'

export function useGenerateCoverLetter() {
  return useMutation({
    mutationFn: (jobId: string) =>
      apiPost<{ cover_letter: string }>(`/jobs/${jobId}/cover-letter`),
  })
}

export function useATSCheck() {
  return useMutation({
    mutationFn: ({ jobId, resumeText }: { jobId: string; resumeText: string }) =>
      apiPost<ATSResult>(`/jobs/${jobId}/ats-check`, { resume_text: resumeText }),
  })
}

export function useScoreJobs() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => apiPost<{ scored: number }>('/jobs/score'),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['jobs'] })
      qc.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}

export function useAnalyzeSkillGaps() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (jobId: string) =>
      apiPost<LearningItem[]>(`/jobs/${jobId}/skill-gaps`),
    onSuccess: (_data, jobId) => {
      qc.invalidateQueries({ queryKey: ['learning-items', jobId] })
    },
  })
}

export function useLearningItems(jobId: string) {
  return useQuery({
    queryKey: ['learning-items', jobId],
    queryFn: () => apiGet<LearningItem[]>(`/jobs/${jobId}/learning-items`),
  })
}

export function useLearningSummary() {
  return useQuery({
    queryKey: ['learning-summary'],
    queryFn: () => apiGet<SkillSummary[]>('/jobs/learning-items/summary'),
  })
}

export function useToggleLearningItem() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ itemId, isKnown }: { itemId: string; isKnown: boolean }) =>
      apiPatch<LearningItem>(`/jobs/learning-items/${itemId}`, { is_known: isKnown }),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['learning-items', data.job_id] })
    },
  })
}
