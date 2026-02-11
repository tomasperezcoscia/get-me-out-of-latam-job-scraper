import { useEffect, useRef } from 'react'
import { X } from 'lucide-react'

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
}

export default function Modal({ open, onClose, title, children }: ModalProps) {
  const ref = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    if (open) {
      el.showModal()
    } else {
      el.close()
    }
  }, [open])

  if (!open) return null

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      className="backdrop:bg-black/40 rounded-xl shadow-xl p-0 w-full max-w-2xl"
    >
      <div className="flex items-center justify-between px-6 py-4 border-b">
        <h2 className="text-lg font-semibold">{title}</h2>
        <button onClick={onClose} className="p-1 rounded hover:bg-gray-100">
          <X className="h-5 w-5" />
        </button>
      </div>
      <div className="px-6 py-4 max-h-[70vh] overflow-y-auto">{children}</div>
    </dialog>
  )
}
