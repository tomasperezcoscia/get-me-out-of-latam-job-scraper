import {
  User,
  MapPin,
  Clock,
  Mail,
  Linkedin,
  Github,
  ExternalLink,
  Briefcase,
  DollarSign,
  Languages,
  AlertCircle,
  BookOpen,
  CheckCircle2,
  Circle,
} from 'lucide-react'
import { useProfile } from '../api/profile'
import { useLearningSummary } from '../api/ai'
import { formatSalary, cn } from '../lib/utils'
import type { SkillSummary } from '../types'
import Badge from '../components/ui/Badge'
import LoadingSpinner from '../components/ui/LoadingSpinner'

function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

export default function Profile() {
  const { data: profile, isLoading, error } = useProfile()
  const { data: skills } = useLearningSummary()

  if (isLoading) return <LoadingSpinner />

  if (error || !profile) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-red-500">
        <AlertCircle className="h-10 w-10 mb-3" />
        <p className="text-lg font-medium">Failed to load profile</p>
        <p className="text-sm text-gray-500 mt-1">
          {error instanceof Error
            ? error.message
            : 'No profile found. Seed your profile first.'}
        </p>
      </div>
    )
  }

  // Group skills by category
  const grouped: Record<string, SkillSummary[]> = {}
  for (const s of skills ?? []) {
    if (!grouped[s.category]) grouped[s.category] = []
    grouped[s.category].push(s)
  }
  const totalSkills = skills?.length ?? 0
  const knownSkills = skills?.filter((s) => s.is_known).length ?? 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <User className="h-7 w-7 text-gray-700" />
        <h1 className="text-2xl font-bold text-gray-900">Profile</h1>
      </div>

      {/* Profile Card */}
      <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
        {/* Top Section: Avatar + Name + Info */}
        <div className="flex items-start gap-5">
          {/* Avatar */}
          <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-white text-xl font-bold">
            {getInitials(profile.full_name)}
          </div>

          <div className="min-w-0 flex-1">
            <h2 className="text-2xl font-bold text-gray-900">
              {profile.full_name}
            </h2>

            <div className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-gray-600">
              {profile.location && (
                <span className="inline-flex items-center gap-1.5">
                  <MapPin className="h-4 w-4 text-gray-400" />
                  {profile.location}
                </span>
              )}
              {profile.timezone && (
                <span className="inline-flex items-center gap-1.5">
                  <Clock className="h-4 w-4 text-gray-400" />
                  {profile.timezone}
                </span>
              )}
              {profile.email && (
                <span className="inline-flex items-center gap-1.5">
                  <Mail className="h-4 w-4 text-gray-400" />
                  {profile.email}
                </span>
              )}
            </div>

            {/* Links Row */}
            <div className="mt-3 flex flex-wrap items-center gap-4">
              {profile.linkedin_url && (
                <a
                  href={profile.linkedin_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-sm font-medium text-indigo-600 hover:text-indigo-800 transition-colors"
                >
                  <Linkedin className="h-4 w-4" />
                  LinkedIn
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
              {profile.github_url && (
                <a
                  href={profile.github_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-sm font-medium text-indigo-600 hover:text-indigo-800 transition-colors"
                >
                  <Github className="h-4 w-4" />
                  GitHub
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
              {profile.portfolio_url && (
                <a
                  href={profile.portfolio_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-sm font-medium text-indigo-600 hover:text-indigo-800 transition-colors"
                >
                  <ExternalLink className="h-4 w-4" />
                  Portfolio
                </a>
              )}
            </div>
          </div>
        </div>

        {/* Divider */}
        <hr className="my-6 border-gray-100" />

        {/* Details Grid */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {/* Skills */}
          <div>
            <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-gray-500 mb-3">
              <Briefcase className="h-4 w-4" />
              Skills
            </h3>
            {profile.primary_skills && profile.primary_skills.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {profile.primary_skills.map((skill) => (
                  <Badge
                    key={skill}
                    className="bg-indigo-50 text-indigo-700"
                  >
                    {skill}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400">No skills listed</p>
            )}
          </div>

          {/* Languages */}
          <div>
            <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-gray-500 mb-3">
              <Languages className="h-4 w-4" />
              Languages
            </h3>
            {profile.languages && profile.languages.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {profile.languages.map((lang) => (
                  <Badge
                    key={lang}
                    className="bg-purple-50 text-purple-700"
                  >
                    {lang}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400">No languages listed</p>
            )}
          </div>

          {/* Salary Range */}
          <div>
            <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-gray-500 mb-3">
              <DollarSign className="h-4 w-4" />
              Desired Salary
            </h3>
            <p className="text-lg font-semibold text-gray-900">
              {formatSalary(
                profile.desired_salary_min,
                profile.desired_salary_max,
              )}
            </p>
          </div>

          {/* Experience */}
          <div>
            <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-gray-500 mb-3">
              <Briefcase className="h-4 w-4" />
              Experience
            </h3>
            <p className="text-lg font-semibold text-gray-900">
              {profile.years_experience !== null
                ? `${profile.years_experience} year${profile.years_experience !== 1 ? 's' : ''}`
                : 'Not specified'}
            </p>
          </div>
        </div>

        {/* Bio */}
        {profile.bio && (
          <>
            <hr className="my-6 border-gray-100" />
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-500 mb-3">
                Bio
              </h3>
              <div className="rounded-lg bg-gray-50 p-4">
                <p className="text-sm leading-relaxed text-gray-700 whitespace-pre-line">
                  {profile.bio}
                </p>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Skills to Learn Section */}
      {totalSkills > 0 && (
        <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <h2 className="flex items-center gap-2 text-lg font-bold text-gray-900">
              <BookOpen className="h-5 w-5" />
              Skills to Learn
            </h2>
            <span className="text-sm text-gray-500">
              {knownSkills} of {totalSkills} covered
            </span>
          </div>

          {/* Progress bar */}
          <div className="w-full bg-gray-200 rounded-full h-2 mb-6">
            <div
              className="bg-green-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${totalSkills > 0 ? (knownSkills / totalSkills) * 100 : 0}%` }}
            />
          </div>

          {/* Grouped by category */}
          <div className="space-y-6">
            {Object.entries(grouped).map(([category, items]) => (
              <div key={category}>
                <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-3">
                  {category}
                </h3>
                <div className="space-y-2">
                  {items.map((item) => (
                    <div
                      key={item.skill}
                      className={cn(
                        'flex items-start gap-3 p-3 rounded-lg',
                        item.is_known ? 'bg-green-50' : 'bg-gray-50'
                      )}
                    >
                      <div className="mt-0.5 shrink-0">
                        {item.is_known ? (
                          <CheckCircle2 className="h-5 w-5 text-green-500" />
                        ) : (
                          <Circle className="h-5 w-5 text-gray-300" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className={cn(
                            'text-sm font-medium',
                            item.is_known ? 'text-green-700 line-through' : 'text-gray-900'
                          )}>
                            {item.skill}
                          </p>
                          <Badge className="bg-blue-100 text-blue-700 text-xs">
                            {item.job_count} job{item.job_count !== 1 ? 's' : ''}
                          </Badge>
                        </div>
                        <ul className="mt-1 space-y-0.5">
                          {item.details.map((detail, i) => (
                            <li
                              key={i}
                              className={cn(
                                'text-xs',
                                item.is_known ? 'text-green-600 line-through' : 'text-gray-500'
                              )}
                            >
                              {detail}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
