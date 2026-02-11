export function formatSalary(min: number | null, max: number | null, currency = 'USD'): string {
  if (!min && !max) return 'Not specified'
  const fmt = (n: number) => {
    if (n >= 1000) return `${Math.round(n / 1000)}k`
    return String(n)
  }
  const sym = currency === 'USD' ? '$' : currency === 'EUR' ? '\u20AC' : currency
  if (min && max) return `${sym}${fmt(min)} - ${sym}${fmt(max)}`
  if (min) return `${sym}${fmt(min)}+`
  return `Up to ${sym}${fmt(max!)}`
}

export function formatDate(iso: string | null): string {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export function relativeTime(iso: string | null): string {
  if (!iso) return ''
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}d ago`
  return formatDate(iso)
}

export function scoreColor(score: number | null): string {
  if (score === null) return 'text-gray-400'
  if (score >= 75) return 'text-emerald-600'
  if (score >= 50) return 'text-amber-500'
  return 'text-red-500'
}

export function scoreBg(score: number | null): string {
  if (score === null) return 'bg-gray-100'
  if (score >= 75) return 'bg-emerald-50'
  if (score >= 50) return 'bg-amber-50'
  return 'bg-red-50'
}

export function statusColor(status: string): string {
  const map: Record<string, string> = {
    new: 'bg-blue-100 text-blue-800',
    reviewed: 'bg-purple-100 text-purple-800',
    applied: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
    interview: 'bg-amber-100 text-amber-800',
    offer: 'bg-emerald-100 text-emerald-800',
  }
  return map[status] || 'bg-gray-100 text-gray-800'
}

export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(' ')
}
