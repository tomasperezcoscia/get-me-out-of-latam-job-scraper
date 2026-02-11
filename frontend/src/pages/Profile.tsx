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
} from 'lucide-react'
import { useProfile } from '../api/profile'
import { formatSalary } from '../lib/utils'
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
    </div>
  )
}
