export type JobStatus = 'new' | 'reviewed' | 'applied' | 'rejected' | 'interview' | 'offer'

export interface Job {
  id: string
  title: string
  company: string
  location: string | null
  salary_min: number | null
  salary_max: number | null
  salary_currency: string
  description: string
  requirements: string | null
  url: string
  source: string | null
  posted_at: string | null
  scraped_at: string
  is_remote: boolean
  tags: string[] | null
  match_score: number | null
  status: JobStatus
  notes: string | null
}

export interface JobListResponse {
  items: Job[]
  total: number
  skip: number
  limit: number
}

export interface JobFilters {
  status?: string
  source?: string
  min_score?: number
  min_salary?: number
  search?: string
  skip?: number
  limit?: number
}

export interface Stats {
  total_jobs: number
  by_source: Record<string, number>
  by_status: Record<string, number>
  jobs_with_salary: number
  avg_salary_min: number | null
  avg_salary_max: number | null
}

export interface Profile {
  id: string
  full_name: string
  email: string | null
  location: string | null
  timezone: string | null
  linkedin_url: string | null
  github_url: string | null
  portfolio_url: string | null
  primary_skills: string[] | null
  years_experience: number | null
  desired_salary_min: number | null
  desired_salary_max: number | null
  languages: string[] | null
  bio: string | null
}

export interface CollectResult {
  source: string
  fetched: number
  inserted: number
}

export interface Application {
  id: string
  job_id: string
  applied_at: string
  cover_letter: string | null
  resume_version: string | null
  status: string
  follow_up_date: string | null
  interview_notes: string | null
  notes: string | null
  created_at: string
}

export interface ATSResult {
  ats_score: number | null
  missing_keywords: string[]
  present_keywords: string[]
  suggestions: string[]
}

// --- Mass Apply ---

export interface MassApplyStarted {
  task_id: string
  total: number
}

export interface MassApplyProgress {
  task_id: string
  total: number
  completed: number
  failed: number
  current_job: string | null
  results: MassApplyJobResult[]
  done: boolean
}

export interface MassApplyJobResult {
  job_id: string
  job_title: string
  status: 'done' | 'failed' | 'skipped'
  error?: string
}

// --- Learning Items ---

export interface LearningItem {
  id: string
  job_id: string
  skill: string
  detail: string
  category: string
  is_known: boolean
}
