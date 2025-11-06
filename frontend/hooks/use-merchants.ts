import { useQuery } from "@tanstack/react-query"
import apiClient from "@/lib/api"
import type { MerchantFilters, TransactionFilters } from "@/lib/types"

export function useMerchants(filters?: MerchantFilters) {
  return useQuery({
    queryKey: ["merchants", filters],
    queryFn: () => apiClient.getMerchants(filters),
    staleTime: 300000, // 5 minutes (merchants change less frequently)
  })
}

export function useMerchant(id: string) {
  return useQuery({
    queryKey: ["merchant", id],
    queryFn: () => apiClient.getMerchant(id),
    enabled: !!id,
    staleTime: 300000,
  })
}

export function useMerchantTransactions(
  id: string,
  filters?: TransactionFilters
) {
  return useQuery({
    queryKey: ["merchant-transactions", id, filters],
    queryFn: () => apiClient.getMerchantTransactions(id, filters),
    enabled: !!id,
    staleTime: 30000,
  })
}

export function useCategories(
  period?: string,
  start_date?: string,
  end_date?: string
) {
  return useQuery({
    queryKey: ["categories", period, start_date, end_date],
    queryFn: () => apiClient.getCategories(period, start_date, end_date),
    staleTime: 300000,
  })
}
