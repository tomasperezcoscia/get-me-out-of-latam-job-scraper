import { scoreColor, scoreBg } from '../../lib/utils'

interface ScoreIndicatorProps {
  score: number | null
  size?: 'sm' | 'md' | 'lg'
}

export default function ScoreIndicator({ score, size = 'md' }: ScoreIndicatorProps) {
  const sizeClasses = {
    sm: 'h-8 w-8 text-xs',
    md: 'h-10 w-10 text-sm',
    lg: 'h-14 w-14 text-lg',
  }

  return (
    <div
      className={`${sizeClasses[size]} ${scoreBg(score)} ${scoreColor(score)} rounded-full flex items-center justify-center font-bold`}
    >
      {score !== null ? Math.round(score) : '?'}
    </div>
  )
}
