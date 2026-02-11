import { useState, useCallback } from 'react'

export function useJobSelection() {
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const toggle = useCallback((id: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }, [])

  const selectAll = useCallback((ids: string[]) => {
    setSelected((prev) => {
      const next = new Set(prev)
      for (const id of ids) next.add(id)
      return next
    })
  }, [])

  const clearAll = useCallback(() => {
    setSelected(new Set())
  }, [])

  const isSelected = useCallback((id: string) => selected.has(id), [selected])

  return { selected, toggle, selectAll, clearAll, isSelected, count: selected.size }
}
