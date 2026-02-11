import { DollarSign } from 'lucide-react'
import { formatSalary } from '../../lib/utils'

interface SalaryRangeProps {
  min: number | null
  max: number | null
  currency?: string
}

export default function SalaryRange({ min, max, currency = 'USD' }: SalaryRangeProps) {
  const text = formatSalary(min, max, currency)
  if (text === 'Not specified') return <span className="text-gray-400 text-sm">{text}</span>

  return (
    <span className="inline-flex items-center gap-1 text-sm font-medium text-emerald-700">
      <DollarSign className="h-3.5 w-3.5" />
      {text}
    </span>
  )
}
