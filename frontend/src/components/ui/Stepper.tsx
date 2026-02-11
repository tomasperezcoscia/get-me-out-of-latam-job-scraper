import { Check } from 'lucide-react'

interface StepperProps {
  steps: string[]
  current: number
}

export default function Stepper({ steps, current }: StepperProps) {
  return (
    <div className="flex items-center gap-2 mb-6">
      {steps.map((label, i) => (
        <div key={label} className="flex items-center gap-2">
          <div
            className={`flex items-center justify-center h-7 w-7 rounded-full text-xs font-bold ${
              i < current
                ? 'bg-emerald-500 text-white'
                : i === current
                  ? 'bg-gray-900 text-white'
                  : 'bg-gray-200 text-gray-500'
            }`}
          >
            {i < current ? <Check className="h-4 w-4" /> : i + 1}
          </div>
          <span className={`text-sm ${i <= current ? 'text-gray-900 font-medium' : 'text-gray-400'}`}>
            {label}
          </span>
          {i < steps.length - 1 && <div className="w-8 h-px bg-gray-300" />}
        </div>
      ))}
    </div>
  )
}
