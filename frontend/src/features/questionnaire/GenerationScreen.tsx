import { CheckCircle, Download, AlertCircle, RefreshCw } from 'lucide-react'
import type { GenerateResult } from './types'
import { getDownloadUrl } from './api/questionnaire'

type GenerationState = 'generating' | 'success' | 'error'

interface GenerationScreenProps {
  state: GenerationState
  result: GenerateResult | null
  error: string | null
  onRetry: () => void
}

const GenerationScreen = ({ state, result, error, onRetry }: GenerationScreenProps) => (
  <div className="min-h-screen bg-background flex flex-col items-center justify-center px-6 text-center">
    {state === 'generating' && (
      <>
        {/* Spinning animation */}
        <div className="relative mb-6">
          <div className="h-16 w-16 rounded-full border-4 border-muted border-t-primary animate-spin" />
        </div>
        <h2 className="text-xl font-semibold mb-2">Creating your personalized plan…</h2>
        <p className="text-sm text-muted-foreground">This may take a moment</p>
      </>
    )}

    {state === 'success' && result && (
      <>
        <div className="rounded-full bg-green-100 p-5 mb-6">
          <CheckCircle size={40} className="text-green-600" />
        </div>
        <h2 className="text-xl font-semibold mb-6">Your plan is ready!</h2>

        <div className="w-full max-w-sm space-y-3">
          {/* Plan activated */}
          <div className="flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 px-4 py-3">
            <CheckCircle size={18} className="text-green-600 flex-shrink-0" />
            <p className="text-sm font-medium text-green-800">Plan activated in the app</p>
          </div>

          {/* Download link */}
          <a
            href={getDownloadUrl(result.xlsx_token)}
            download
            className="flex items-center justify-center gap-2 w-full rounded-lg border border-primary bg-primary/5 text-primary px-4 py-3 text-sm font-medium min-h-[52px] hover:bg-primary/10 transition-colors"
          >
            <Download size={18} />
            Download as Excel (.xlsx)
          </a>
        </div>
      </>
    )}

    {state === 'error' && (
      <>
        <div className="rounded-full bg-red-100 p-5 mb-6">
          <AlertCircle size={40} className="text-red-500" />
        </div>
        <h2 className="text-xl font-semibold mb-2">Something went wrong</h2>
        <p className="text-sm text-muted-foreground mb-6">
          {error ?? 'Could not generate your plan. Please try again.'}
        </p>
        <button
          type="button"
          onClick={onRetry}
          className="flex items-center gap-2 bg-primary text-primary-foreground rounded-lg px-6 py-3 font-medium min-h-[44px] hover:bg-primary/90 transition-colors"
        >
          <RefreshCw size={16} />
          Try again
        </button>
      </>
    )}
  </div>
)

export default GenerationScreen
