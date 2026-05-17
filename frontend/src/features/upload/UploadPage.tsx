import { useState, useRef } from 'react'
import { CheckCircle, AlertCircle, FileSpreadsheet, Sparkles, Brain } from 'lucide-react'
import { cn } from '@/lib/utils'
import { uploadApi, agentApi } from '@/lib/api'
import { useQueryClient } from '@tanstack/react-query'
import type { UploadResponse, IngestResponse } from '@/types'

type Tab = 'ai' | 'classic'

const UploadPage = () => {
  const [tab, setTab] = useState<Tab>('ai')
  const [isDragging, setIsDragging] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [classicResult, setClassicResult] = useState<UploadResponse | null>(null)
  const [aiResult, setAiResult] = useState<IngestResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [rotationStartDate, setRotationStartDate] = useState(
    new Date().toISOString().split('T')[0]
  )
  const inputRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()

  const reset = () => {
    setError(null)
    setClassicResult(null)
    setAiResult(null)
  }

  const handleFile = async (file: File) => {
    reset()
    if (tab === 'classic' && !file.name.endsWith('.xlsx')) {
      setError('Classic upload only accepts .xlsx files.')
      return
    }
    if (tab === 'ai' && !file.name.endsWith('.xlsx') && !file.name.endsWith('.json')) {
      setError('AI ingest accepts .xlsx or .json files.')
      return
    }

    setIsProcessing(true)
    try {
      if (tab === 'ai') {
        const data = await agentApi.ingest(file, rotationStartDate)
        setAiResult(data)
      } else {
        const data = await uploadApi.uploadPlan(file, rotationStartDate)
        setClassicResult(data)
      }
      queryClient.invalidateQueries()
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? 'Upload failed. Please try again.')
    } finally {
      setIsProcessing(false)
    }
  }

  const processingLabel = tab === 'ai'
    ? 'AI is reading your plan — this takes 15–30 seconds…'
    : 'Parsing workbook…'

  const acceptedTypes = tab === 'ai' ? '.xlsx,.json' : '.xlsx'

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-base font-semibold">Upload Plan</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Import your longevity workbook. A new upload replaces the current plan.
        </p>
      </div>

      {/* Tab switcher */}
      <div className="flex rounded-xl border border-border overflow-hidden">
        <button
          type="button"
          onClick={() => { setTab('ai'); reset() }}
          className={cn(
            'flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium transition-colors',
            tab === 'ai'
              ? 'bg-primary text-primary-foreground'
              : 'bg-background text-muted-foreground hover:bg-accent/30',
          )}
        >
          <Brain size={15} />
          AI Ingest
        </button>
        <button
          type="button"
          onClick={() => { setTab('classic'); reset() }}
          className={cn(
            'flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium transition-colors border-l border-border',
            tab === 'classic'
              ? 'bg-primary text-primary-foreground'
              : 'bg-background text-muted-foreground hover:bg-accent/30',
          )}
        >
          <FileSpreadsheet size={15} />
          Classic Upload
        </button>
      </div>

      {/* Tab description */}
      {tab === 'ai' ? (
        <div className="rounded-lg bg-primary/5 border border-primary/20 p-3 text-xs text-primary space-y-1">
          <p className="font-semibold flex items-center gap-1.5"><Sparkles size={12} /> AI-powered — no column mapping required</p>
          <p className="text-muted-foreground">
            Claude reads your spreadsheet or JSON regardless of column names or layout changes.
            Generates a 30-day todo list automatically. Accepts <strong>.xlsx</strong> or <strong>.json</strong>.
          </p>
        </div>
      ) : (
        <div className="rounded-lg bg-muted/40 border border-border p-3 text-xs text-muted-foreground space-y-1">
          <p className="font-semibold text-foreground">Rule-based column mapping</p>
          <p>Parses .xlsx directly without AI. Faster but requires column headers to match known names.</p>
        </div>
      )}

      {/* Drop zone */}
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={e => {
          e.preventDefault()
          setIsDragging(false)
          const file = e.dataTransfer.files[0]
          if (file) handleFile(file)
        }}
        disabled={isProcessing}
        className={cn(
          'w-full border-2 border-dashed rounded-xl p-10 flex flex-col items-center gap-3 transition-colors',
          isDragging ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50 hover:bg-accent/20',
          isProcessing && 'opacity-50 cursor-wait',
        )}
      >
        {isProcessing ? (
          <>
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-muted-foreground">{processingLabel}</span>
          </>
        ) : (
          <>
            {tab === 'ai' ? <Brain size={36} className="text-primary/60" /> : <FileSpreadsheet size={36} className="text-muted-foreground" />}
            <div className="text-center">
              <p className="text-sm font-medium">
                Drop your {tab === 'ai' ? '.xlsx or .json' : '.xlsx'} file here
              </p>
              <p className="text-xs text-muted-foreground mt-1">or click to browse</p>
            </div>
          </>
        )}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={acceptedTypes}
        className="hidden"
        onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])}
      />

      {/* AI ingest success */}
      {aiResult && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4 space-y-2">
          <div className="flex items-center gap-2">
            <CheckCircle size={16} className="text-green-600" />
            <span className="text-sm font-semibold text-green-800">
              Plan ingested — {aiResult.plan_name}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-sm text-green-700">
            <p>{aiResult.tasks_imported} tasks imported</p>
            <p>{aiResult.rotation_days_imported} rotation days</p>
            <p>{aiResult.screenings_imported} screenings</p>
            <p>{aiResult.todos_prefilled} todos pre-generated (30 days)</p>
          </div>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {aiResult.pillars_found.map(p => (
              <span key={p} className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full capitalize">
                {p.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Classic upload success */}
      {classicResult && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4 space-y-2">
          <div className="flex items-center gap-2">
            <CheckCircle size={16} className="text-green-600" />
            <span className="text-sm font-semibold text-green-800">Plan uploaded successfully</span>
          </div>
          <p className="text-sm text-green-700">{classicResult.tasks_imported} tasks imported</p>
          {classicResult.rotation_days_imported > 0 && (
            <p className="text-sm text-green-700">
              {classicResult.rotation_days_imported} rotation days (starts {rotationStartDate})
            </p>
          )}
          <div className="flex flex-wrap gap-1.5">
            {classicResult.pillars_found.map(p => (
              <span key={p} className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full capitalize">
                {p.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 flex items-start gap-2">
          <AlertCircle size={16} className="text-red-500 shrink-0 mt-0.5" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Rotation start date */}
      <div className="rounded-lg border border-border p-4 space-y-2">
        <p className="text-sm font-medium">30-Day Rotation Start Date</p>
        <p className="text-xs text-muted-foreground">
          Sets Day 1 of your exercise rotation. You can also change this in the Exercise tab after upload.
        </p>
        <input
          type="date"
          value={rotationStartDate}
          onChange={e => setRotationStartDate(e.target.value)}
          className="rounded-lg border border-border px-3 py-1.5 text-sm w-full focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      {/* Tips */}
      {tab === 'ai' ? (
        <div className="rounded-lg bg-muted/50 p-4 text-xs text-muted-foreground space-y-1">
          <p className="font-medium text-foreground text-sm mb-2">AI ingest tips</p>
          <p>• Works with any column names — no mapping required</p>
          <p>• Supports any version of your workbook (v3, v4, future)</p>
          <p>• Also accepts JSON if you prefer to export from Excel first</p>
          <p>• Takes 15–30 seconds for a full workbook (Claude reads every sheet)</p>
          <p>• 30 days of todos are pre-generated immediately after ingest</p>
        </div>
      ) : (
        <div className="rounded-lg bg-muted/50 p-4 text-xs text-muted-foreground space-y-1">
          <p className="font-medium text-foreground text-sm mb-2">Classic upload tips</p>
          <p>• Sheet names become pillar names (e.g. "09_Supplements" → supplements)</p>
          <p>• Header row is auto-detected — title rows are skipped</p>
          <p>• Required column: Name (or Activity, Task, Item, Block, etc.)</p>
          <p>• Unknown columns are saved as metadata — nothing is dropped</p>
        </div>
      )}
    </div>
  )
}

export default UploadPage
