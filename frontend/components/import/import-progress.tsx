"use client"

import { useEffect } from "react"
import { useImportStatus } from "@/hooks/use-imports"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, Clock, AlertCircle, Loader2 } from "lucide-react"
import type { ImportState } from "@/lib/types"

interface ImportProgressProps {
  importId: string
  onComplete?: () => void
}

const stateConfig: Record<ImportState, {
  label: string
  icon: React.ElementType
  color: string
  progress: number
}> = {
  uploaded: { label: "Uploaded", icon: Clock, color: "text-blue-600", progress: 10 },
  parsing: { label: "Parsing CSV", icon: Loader2, color: "text-blue-600", progress: 30 },
  parsed: { label: "Parsed", icon: CheckCircle, color: "text-green-600", progress: 50 },
  enriching: { label: "AI Enriching", icon: Loader2, color: "text-purple-600", progress: 70 },
  enriched: { label: "Enriched", icon: CheckCircle, color: "text-green-600", progress: 90 },
  completed: { label: "Completed", icon: CheckCircle, color: "text-green-600", progress: 100 },
  failed: { label: "Failed", icon: AlertCircle, color: "text-red-600", progress: 0 },
}

export function ImportProgress({ importId, onComplete }: ImportProgressProps) {
  const { data: importData, isLoading } = useImportStatus(importId, true)

  useEffect(() => {
    if (importData?.state === "completed" && onComplete) {
      // Delay callback to show completion state
      const timer = setTimeout(() => onComplete(), 2000)
      return () => clearTimeout(timer)
    }
  }, [importData?.state, onComplete])

  if (isLoading || !importData) {
    return (
      <Card>
        <CardContent className="py-6">
          <div className="flex items-center justify-center gap-2">
            <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
            <span className="text-sm text-muted-foreground">Loading status...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  const config = stateConfig[importData.state as ImportState]
  const Icon = config.icon
  const isProcessing = ["parsing", "enriching"].includes(importData.state)
  const isComplete = importData.state === "completed"
  const isFailed = importData.state === "failed"

  return (
    <Card className={isFailed ? "border-red-200" : isComplete ? "border-green-200" : ""}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Import Progress</CardTitle>
          <Badge variant={isComplete ? "default" : isFailed ? "destructive" : "secondary"}>
            <Icon className={`h-3 w-3 mr-1 ${isProcessing ? "animate-spin" : ""}`} />
            {config.label}
          </Badge>
        </div>
        <CardDescription>Import ID: {importId}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Progress</span>
            <span className="font-medium">{config.progress}%</span>
          </div>
          <div className="w-full bg-secondary rounded-full h-2.5">
            <div
              className={`h-2.5 rounded-full transition-all duration-500 ${
                isFailed ? "bg-red-600" : isComplete ? "bg-green-600" : "bg-blue-600"
              }`}
              style={{ width: `${config.progress}%` }}
            />
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Total Rows</p>
            <p className="text-2xl font-bold">{importData.total_rows || 0}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Parsed</p>
            <p className="text-2xl font-bold text-blue-600">{importData.parsed_rows || 0}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Enriched</p>
            <p className="text-2xl font-bold text-purple-600">{importData.enriched_rows || 0}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Failed</p>
            <p className="text-2xl font-bold text-red-600">{importData.failed_rows || 0}</p>
          </div>
        </div>

        {/* Status Messages */}
        {isProcessing && (
          <div className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-950 rounded-lg">
            <Loader2 className="h-4 w-4 animate-spin text-blue-600 mt-0.5" />
            <div className="text-sm text-blue-900 dark:text-blue-100">
              {importData.state === "parsing" && "Parsing CSV and detecting duplicates..."}
              {importData.state === "enriching" && "AI is enriching transactions with merchant data, categories, and tags..."}
            </div>
          </div>
        )}

        {isComplete && (
          <div className="flex items-start gap-2 p-3 bg-green-50 dark:bg-green-950 rounded-lg">
            <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
            <div className="text-sm text-green-900 dark:text-green-100">
              <p className="font-medium">Import completed successfully!</p>
              <p className="mt-1">Your transactions are now available in the dashboard.</p>
            </div>
          </div>
        )}

        {isFailed && importData.errors && importData.errors.length > 0 && (
          <div className="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-950 rounded-lg">
            <AlertCircle className="h-4 w-4 text-red-600 mt-0.5" />
            <div className="text-sm text-red-900 dark:text-red-100">
              <p className="font-medium">Import failed</p>
              <p className="mt-1">{importData.errors[0]?.error_message || "Unknown error"}</p>
            </div>
          </div>
        )}

        {/* Duration */}
        {importData.duration_ms && (
          <div className="text-xs text-muted-foreground text-center pt-2 border-t">
            Processing time: {(importData.duration_ms / 1000).toFixed(1)}s
          </div>
        )}
      </CardContent>
    </Card>
  )
}
