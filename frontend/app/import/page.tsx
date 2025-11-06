"use client"

import { useState } from "react"
import { useUploadCSV } from "@/hooks/use-imports"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Upload, FileText, CheckCircle, AlertCircle, Loader2 } from "lucide-react"
import type { SourceBank } from "@/lib/types"

export default function ImportPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedBank, setSelectedBank] = useState<SourceBank | "">("")
  const uploadMutation = useUploadCSV()

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && file.type === "text/csv") {
      setSelectedFile(file)
    } else {
      alert("Please select a valid CSV file")
    }
  }

  const handleUpload = async () => {
    if (!selectedFile || !selectedBank) {
      alert("Please select both a file and a bank")
      return
    }

    uploadMutation.mutate(
      { file: selectedFile, sourceBank: selectedBank as SourceBank },
      {
        onSuccess: (data) => {
          setSelectedFile(null)
          setSelectedBank("")
          // Reset file input
          const fileInput = document.getElementById("file-upload") as HTMLInputElement
          if (fileInput) fileInput.value = ""
        },
      }
    )
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Import Transactions</h2>
        <p className="text-muted-foreground">
          Upload CSV files from your banks to import transactions
        </p>
      </div>

      {/* Upload Card */}
      <Card>
        <CardHeader>
          <CardTitle>Upload CSV File</CardTitle>
          <CardDescription>
            Select a CSV file from AMEX, Citi, or Wells Fargo
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Bank Selection */}
          <div className="space-y-2">
            <Label htmlFor="bank-select">Source Bank</Label>
            <select
              id="bank-select"
              className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              value={selectedBank}
              onChange={(e) => setSelectedBank(e.target.value as SourceBank | "")}
              disabled={uploadMutation.isPending}
            >
              <option value="">Select a bank...</option>
              <option value="amex">American Express (AMEX)</option>
              <option value="citi">Citibank</option>
              <option value="wells">Wells Fargo</option>
            </select>
          </div>

          {/* File Upload */}
          <div className="space-y-2">
            <Label htmlFor="file-upload">CSV File</Label>
            <div className="flex items-center gap-4">
              <input
                id="file-upload"
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                disabled={uploadMutation.isPending}
              />
            </div>
            {selectedFile && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <FileText className="h-4 w-4" />
                <span>{selectedFile.name}</span>
                <span className="text-xs">
                  ({(selectedFile.size / 1024).toFixed(2)} KB)
                </span>
              </div>
            )}
          </div>

          {/* Upload Button */}
          <Button
            onClick={handleUpload}
            disabled={!selectedFile || !selectedBank || uploadMutation.isPending}
            className="w-full"
            size="lg"
          >
            {uploadMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Upload and Process
              </>
            )}
          </Button>

          {/* Status Messages */}
          {uploadMutation.isSuccess && (
            <div className="flex items-center gap-2 p-4 bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded-lg">
              <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
              <div>
                <p className="font-medium text-green-900 dark:text-green-100">
                  Upload Successful!
                </p>
                <p className="text-sm text-green-700 dark:text-green-300">
                  Import ID: {uploadMutation.data.import_id}
                </p>
                <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                  Your file is being processed in the background. Check the dashboard
                  for updated transactions.
                </p>
              </div>
            </div>
          )}

          {uploadMutation.isError && (
            <div className="flex items-center gap-2 p-4 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg">
              <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
              <div>
                <p className="font-medium text-red-900 dark:text-red-100">
                  Upload Failed
                </p>
                <p className="text-sm text-red-700 dark:text-red-300">
                  {uploadMutation.error instanceof Error
                    ? uploadMutation.error.message
                    : "An error occurred during upload"}
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Instructions Card */}
      <Card>
        <CardHeader>
          <CardTitle>Import Instructions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-medium mb-2 flex items-center gap-2">
              <Badge>AMEX</Badge> American Express
            </h4>
            <p className="text-sm text-muted-foreground">
              Download your transaction history from the AMEX website. The file
              should be in CSV format with headers including Date, Description,
              Amount, and Reference.
            </p>
          </div>

          <div>
            <h4 className="font-medium mb-2 flex items-center gap-2">
              <Badge>Citi</Badge> Citibank
            </h4>
            <p className="text-sm text-muted-foreground">
              Export transactions from Citi online banking. The CSV should include
              Date, Description, Debit, Credit, and Member columns.
            </p>
          </div>

          <div>
            <h4 className="font-medium mb-2 flex items-center gap-2">
              <Badge>Wells</Badge> Wells Fargo
            </h4>
            <p className="text-sm text-muted-foreground">
              Download your Wells Fargo checking account transactions. The file
              should be a CSV with Date, Amount, and Description in that order
              (no headers required).
            </p>
          </div>

          <div className="pt-4 border-t">
            <h4 className="font-medium mb-2">Processing</h4>
            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
              <li>Files are processed in the background by our worker service</li>
              <li>Duplicates are automatically detected and skipped</li>
              <li>
                AI enrichment adds merchant details, categories, and tags
              </li>
              <li>Processing typically takes 1-5 minutes depending on file size</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
