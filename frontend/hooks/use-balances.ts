import { useQuery } from "@tanstack/react-query"
import apiClient from "@/lib/api"
import type { SourceBank } from "@/lib/types"

export function useAllBalances() {
  return useQuery({
    queryKey: ["balances"],
    queryFn: () => apiClient.getAllBalances(),
    staleTime: 60000, // 1 minute
    refetchInterval: 120000, // Refetch every 2 minutes
  })
}

export function useBalanceByBank(bank: SourceBank) {
  return useQuery({
    queryKey: ["balance", bank],
    queryFn: () => apiClient.getBalanceByBank(bank),
    enabled: !!bank,
    staleTime: 60000,
  })
}
