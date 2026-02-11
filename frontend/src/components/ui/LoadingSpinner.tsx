import { Loader2 } from 'lucide-react'

export default function LoadingSpinner({ className = '' }: { className?: string }) {
  return (
    <div className={`flex items-center justify-center py-12 ${className}`}>
      <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
    </div>
  )
}
