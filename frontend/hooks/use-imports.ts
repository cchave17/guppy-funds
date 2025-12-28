import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import apiClient from "@/lib/api"
import type { SourceBank } from "@/lib/types"

export function useImportStatus(importId: string | null, enabled: boolean = true) {
  return useQuery({
    queryKey: ["import-status", importId],
    queryFn: () => apiClient.getImportStatus(importId!),
    enabled: enabled && !!importId,
    refetchInterval: (query) => {
      // Stop polling if import is completed or failed
      if (query.state.data?.state === "completed" || query.state.data?.state === "failed") {
        return false
      }
      // Poll every 2 seconds while processing
      return 2000
    },
    staleTime: 0, // Always fetch fresh data
  })
}

export function useUploadCSV() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ file, sourceBank }: { file: File; sourceBank: SourceBank }) =>
      apiClient.uploadCSV(file, sourceBank),
    onSuccess: () => {
      // Invalidate transactions and balances after successful upload
      queryClient.invalidateQueries({ queryKey: ["transactions"] })
      queryClient.invalidateQueries({ queryKey: ["balances"] })
      queryClient.invalidateQueries({ queryKey: ["merchants"] })
      queryClient.invalidateQueries({ queryKey: ["transaction-summary"] })
    },
  })
}

export function useParseImport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (importId: string) => apiClient.parseImport(importId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] })
    },
  })
}

export function useEnrichImport() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (importId: string) => apiClient.enrichImport(importId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] })
      queryClient.invalidateQueries({ queryKey: ["balances"] })
      queryClient.invalidateQueries({ queryKey: ["merchants"] })
      queryClient.invalidateQueries({ queryKey: ["transaction-summary"] })
    },
  })
}
