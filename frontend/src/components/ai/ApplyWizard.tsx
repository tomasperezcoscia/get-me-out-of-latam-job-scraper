import { useState } from 'react'
import { Loader2, CheckCircle } from 'lucide-react'
import { useGenerateCoverLetter } from '../../api/ai'
import { useCreateApplication } from '../../api/applications'
import Modal from '../ui/Modal'
import Stepper from '../ui/Stepper'

interface ApplyWizardProps {
  open: boolean
  onClose: () => void
  jobId: string
  jobTitle: string
}

const STEPS = ['Cover Letter', 'Review', 'Confirm']

export default function ApplyWizard({ open, onClose, jobId, jobTitle }: ApplyWizardProps) {
  const [step, setStep] = useState(0)
  const [coverLetter, setCoverLetter] = useState('')
  const [done, setDone] = useState(false)

  const generate = useGenerateCoverLetter()
  const apply = useCreateApplication()

  const handleGenerate = () => {
    generate.mutate(jobId, {
      onSuccess: (data) => {
        setCoverLetter(data.cover_letter)
        setStep(1)
      },
    })
  }

  const handleApply = () => {
    apply.mutate(
      { job_id: jobId, cover_letter: coverLetter || undefined },
      {
        onSuccess: () => {
          setDone(true)
          setStep(2)
        },
      },
    )
  }

  const handleClose = () => {
    setStep(0)
    setCoverLetter('')
    setDone(false)
    generate.reset()
    apply.reset()
    onClose()
  }

  return (
    <Modal open={open} onClose={handleClose} title={`Apply: ${jobTitle}`}>
      <Stepper steps={STEPS} current={step} />

      {/* Step 0: Generate Cover Letter */}
      {step === 0 && (
        <div>
          <p className="text-sm text-gray-500 mb-4">
            Generate a personalized cover letter, or skip to apply without one.
          </p>
          <div className="flex gap-2">
            <button
              onClick={handleGenerate}
              disabled={generate.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800 disabled:opacity-50"
            >
              {generate.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Generate Cover Letter
            </button>
            <button
              onClick={() => setStep(1)}
              className="px-4 py-2 border rounded-lg text-sm font-medium hover:bg-gray-50"
            >
              Skip
            </button>
          </div>
          {generate.isError && (
            <div className="bg-red-50 text-red-700 rounded-lg p-3 text-sm mt-3">
              {generate.error?.message || 'Generation failed'}
            </div>
          )}
        </div>
      )}

      {/* Step 1: Review */}
      {step === 1 && (
        <div>
          {coverLetter ? (
            <>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Cover Letter (editable)
              </label>
              <textarea
                value={coverLetter}
                onChange={(e) => setCoverLetter(e.target.value)}
                rows={12}
                className="w-full border rounded-lg p-3 text-sm font-mono resize-y focus:outline-none focus:ring-2 focus:ring-gray-900"
              />
            </>
          ) : (
            <p className="text-sm text-gray-500 mb-4">No cover letter. You can proceed without one.</p>
          )}
          <div className="flex gap-2 mt-3">
            <button
              onClick={handleApply}
              disabled={apply.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50"
            >
              {apply.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Confirm Application
            </button>
            <button
              onClick={() => setStep(0)}
              className="px-4 py-2 border rounded-lg text-sm font-medium hover:bg-gray-50"
            >
              Back
            </button>
          </div>
          {apply.isError && (
            <div className="bg-red-50 text-red-700 rounded-lg p-3 text-sm mt-3">
              {apply.error?.message || 'Application failed'}
            </div>
          )}
        </div>
      )}

      {/* Step 2: Done */}
      {step === 2 && done && (
        <div className="text-center py-8">
          <CheckCircle className="h-12 w-12 text-emerald-500 mx-auto mb-3" />
          <p className="text-lg font-semibold text-gray-900">Application Recorded</p>
          <p className="text-sm text-gray-500 mt-1">
            Job status has been updated to "applied".
          </p>
          <button
            onClick={handleClose}
            className="mt-4 px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800"
          >
            Done
          </button>
        </div>
      )}
    </Modal>
  )
}
