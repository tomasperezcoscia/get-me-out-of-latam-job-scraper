import { ChevronLeft, ChevronRight } from 'lucide-react'

interface PaginationProps {
  total: number
  skip: number
  limit: number
  onChange: (skip: number) => void
}

export default function Pagination({ total, skip, limit, onChange }: PaginationProps) {
  const page = Math.floor(skip / limit) + 1
  const totalPages = Math.ceil(total / limit)

  if (totalPages <= 1) return null

  return (
    <div className="flex items-center justify-between pt-4">
      <p className="text-sm text-gray-500">
        {skip + 1}–{Math.min(skip + limit, total)} of {total}
      </p>
      <div className="flex gap-1">
        <button
          onClick={() => onChange(Math.max(0, skip - limit))}
          disabled={page === 1}
          className="p-1.5 rounded hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        <span className="px-3 py-1 text-sm font-medium">{page} / {totalPages}</span>
        <button
          onClick={() => onChange(skip + limit)}
          disabled={page === totalPages}
          className="p-1.5 rounded hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
