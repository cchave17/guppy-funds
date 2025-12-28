import type {
  Transaction,
  TransactionsResponse,
  TransactionSummary,
  CategoryBreakdown,
  MerchantSpending,
  MonthlyTrend,
  Balance,
  BalanceSummary,
  MerchantsListResponse,
  MerchantDetailsResponse,
  CategoriesResponse,
  Import,
  TransactionFilters,
  MerchantFilters,
  SourceBank,
} from "./types"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  }

  private buildQueryString(params: Record<string, any>): string {
    const filtered = Object.entries(params).filter(
      ([_, value]) => value !== undefined && value !== null && value !== ""
    )
    if (filtered.length === 0) return ""
    const searchParams = new URLSearchParams(
      filtered.map(([key, value]) => [key, String(value)])
    )
    return `?${searchParams.toString()}`
  }

  // Health Check
  async healthCheck(): Promise<{ status: string }> {
    return this.request("/health")
  }

  // ==================
  // Transaction APIs
  // ==================
  async getTransactions(
    filters?: TransactionFilters
  ): Promise<TransactionsResponse> {
    const query = filters ? this.buildQueryString(filters) : ""
    return this.request(`/v1/transactions${query}`)
  }

  async getTransaction(id: string): Promise<Transaction> {
    return this.request(`/v1/transactions/${id}`)
  }

  async getIncomeTransactions(
    filters?: Omit<TransactionFilters, "type">
  ): Promise<TransactionsResponse> {
    const query = filters ? this.buildQueryString(filters) : ""
    return this.request(`/v1/transactions/income${query}`)
  }

  async getExpenseTransactions(
    filters?: Omit<TransactionFilters, "type">
  ): Promise<TransactionsResponse> {
    const query = filters ? this.buildQueryString(filters) : ""
    return this.request(`/v1/transactions/expenses${query}`)
  }

  async getSubscriptions(
    filters?: Omit<TransactionFilters, "is_recurring">
  ): Promise<TransactionsResponse> {
    const query = filters ? this.buildQueryString(filters) : ""
    return this.request(`/v1/transactions/subscriptions${query}`)
  }

  async getTransactionSummary(
    period?: string,
    start_date?: string,
    end_date?: string
  ): Promise<TransactionSummary> {
    const query = this.buildQueryString({ period, start_date, end_date })
    return this.request(`/v1/transactions/summary${query}`)
  }

  async getTransactionsByCategory(
    period?: string,
    start_date?: string,
    end_date?: string,
    limit?: number
  ): Promise<CategoryBreakdown> {
    const query = this.buildQueryString({ period, start_date, end_date, limit })
    return this.request(`/v1/transactions/by-category${query}`)
  }

  async getTransactionsByMerchant(
    period?: string,
    start_date?: string,
    end_date?: string,
    limit?: number
  ): Promise<MerchantSpending> {
    const query = this.buildQueryString({ period, start_date, end_date, limit })
    return this.request(`/v1/transactions/by-merchant${query}`)
  }

  async getTransactionsByMonth(
    start_date?: string,
    end_date?: string
  ): Promise<MonthlyTrend> {
    const query = this.buildQueryString({ start_date, end_date })
    return this.request(`/v1/transactions/by-month${query}`)
  }

  // ==================
  // Balance APIs
  // ==================
  async getAllBalances(): Promise<BalanceSummary> {
    return this.request("/v1/balances")
  }

  async getBalanceByBank(bank: SourceBank): Promise<Balance> {
    return this.request(`/v1/balances/${bank}`)
  }

  // ==================
  // Merchant APIs
  // ==================
  async getMerchants(filters?: MerchantFilters): Promise<MerchantsListResponse> {
    const query = filters ? this.buildQueryString(filters) : ""
    return this.request(`/v1/merchants${query}`)
  }

  async getMerchant(id: string): Promise<MerchantDetailsResponse> {
    return this.request(`/v1/merchants/${id}`)
  }

  async getMerchantTransactions(
    id: string,
    filters?: TransactionFilters
  ): Promise<TransactionsResponse> {
    const query = filters ? this.buildQueryString(filters) : ""
    return this.request(`/v1/merchants/${id}/transactions${query}`)
  }

  async getCategories(
    period?: string,
    start_date?: string,
    end_date?: string
  ): Promise<CategoriesResponse> {
    const query = this.buildQueryString({ period, start_date, end_date })
    return this.request(`/v1/categories${query}`)
  }

  // ==================
  // Import APIs
  // ==================
  async uploadCSV(file: File, sourceBank: SourceBank): Promise<Import> {
    const formData = new FormData()
    formData.append("file", file)
    formData.append("source_bank", sourceBank)

    const url = `${this.baseUrl}/v1/imports`
    const response = await fetch(url, {
      method: "POST",
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || `Upload failed: ${response.statusText}`)
    }

    return response.json()
  }

  async getImportStatus(importId: string): Promise<Import> {
    return this.request(`/v1/imports/${importId}`)
  }

  async parseImport(importId: string): Promise<Import> {
    return this.request(`/v1/imports/${importId}/parse`, {
      method: "POST",
    })
  }

  async enrichImport(importId: string): Promise<Import> {
    return this.request(`/v1/imports/${importId}/enrich`, {
      method: "POST",
    })
  }
}

export const apiClient = new ApiClient()
export default apiClient
