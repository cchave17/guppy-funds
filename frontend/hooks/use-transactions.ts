import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import apiClient from "@/lib/api"
import type { TransactionFilters } from "@/lib/types"

export function useTransactions(filters?: TransactionFilters) {
  return useQuery({
    queryKey: ["transactions", filters],
    queryFn: () => apiClient.getTransactions(filters),
    staleTime: 30000, // 30 seconds
  })
}

export function useTransaction(id: string) {
  return useQuery({
    queryKey: ["transaction", id],
    queryFn: () => apiClient.getTransaction(id),
    enabled: !!id,
  })
}

export function useIncomeTransactions(
  filters?: Omit<TransactionFilters, "type">
) {
  return useQuery({
    queryKey: ["income-transactions", filters],
    queryFn: () => apiClient.getIncomeTransactions(filters),
    staleTime: 30000,
  })
}

export function useExpenseTransactions(
  filters?: Omit<TransactionFilters, "type">
) {
  return useQuery({
    queryKey: ["expense-transactions", filters],
    queryFn: () => apiClient.getExpenseTransactions(filters),
    staleTime: 30000,
  })
}

export function useSubscriptions(
  filters?: Omit<TransactionFilters, "is_recurring">
) {
  return useQuery({
    queryKey: ["subscriptions", filters],
    queryFn: () => apiClient.getSubscriptions(filters),
    staleTime: 30000,
  })
}

export function useTransactionSummary(
  period?: string,
  start_date?: string,
  end_date?: string
) {
  return useQuery({
    queryKey: ["transaction-summary", period, start_date, end_date],
    queryFn: () => apiClient.getTransactionSummary(period, start_date, end_date),
    staleTime: 60000, // 1 minute
  })
}

export function useTransactionsByCategory(
  period?: string,
  start_date?: string,
  end_date?: string,
  limit?: number
) {
  return useQuery({
    queryKey: ["transactions-by-category", period, start_date, end_date, limit],
    queryFn: () =>
      apiClient.getTransactionsByCategory(period, start_date, end_date, limit),
    staleTime: 60000,
  })
}

export function useTransactionsByMerchant(
  period?: string,
  start_date?: string,
  end_date?: string,
  limit?: number
) {
  return useQuery({
    queryKey: ["transactions-by-merchant", period, start_date, end_date, limit],
    queryFn: () =>
      apiClient.getTransactionsByMerchant(period, start_date, end_date, limit),
    staleTime: 60000,
  })
}

export function useTransactionsByMonth(
  start_date?: string,
  end_date?: string
) {
  return useQuery({
    queryKey: ["transactions-by-month", start_date, end_date],
    queryFn: () => apiClient.getTransactionsByMonth(start_date, end_date),
    staleTime: 60000,
  })
}
