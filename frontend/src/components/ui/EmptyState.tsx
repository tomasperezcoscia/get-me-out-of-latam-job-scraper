import { Inbox } from 'lucide-react'

interface EmptyStateProps {
  title?: string
  message?: string
}

export default function EmptyState({ title = 'No results', message = 'Try adjusting your filters.' }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-gray-400">
      <Inbox className="h-12 w-12 mb-3" />
      <p className="text-lg font-medium">{title}</p>
      <p className="text-sm">{message}</p>
    </div>
  )
}
