// Backend API Types

export type SourceBank = "amex" | "citi" | "wells"
export type TransactionType = "debit" | "credit" | "income"
export type ImportState = "uploaded" | "parsing" | "parsed" | "enriching" | "enriched" | "completed" | "failed"
export type DatePeriod = "current_month" | "last_30_days" | "ytd" | "all_time"

// Location
export interface Location {
  address?: string
  city?: string
  state?: string
  postal_code?: string
  country?: string
}

// Merchant
export interface Merchant {
  name: string
  category: string
  subcategory?: string
  location?: Location
}

export interface MerchantDetails {
  merchant_id: string
  name: string
  aliases: string[]
  category: string
  subcategory?: string
  tags: string[]
  website?: string
  contact_info?: {
    phone?: string
    email?: string
    support_url?: string
  }
  location?: Location
  is_subscription: boolean
  enrichment_confidence: number
  enrichment_version: number
  created_at: string
  updated_at: string
}

// Account
export interface Account {
  name?: string
  account_number?: string
  card_member?: string
}

// Transaction
export interface Transaction {
  transaction_id: string
  source_bank: SourceBank
  import_id: string
  raw_id: string
  enrichment_version: number
  date: string
  description: string
  amount: number
  type: TransactionType
  currency: string
  merchant: Merchant
  account: Account
  tags: string[]
  notes?: string
  is_recurring: boolean
  enriched_confidence: number
  created_at: string
  updated_at: string
}

// Import
export interface Import {
  import_id: string
  source_bank: SourceBank
  file_name: string
  file_path: string
  upload_time: string
  state: ImportState
  total_rows: number
  parsed_rows: number
  enriched_rows: number
  failed_rows: number
  started_at?: string
  completed_at?: string
  duration_ms?: number
  errors: ImportError[]
  enrichment_version: number
  notes?: string
  checksum: string
}

export interface ImportError {
  row_number?: number
  error_message: string
  raw_data?: Record<string, any>
}

// API Response Types
export interface TransactionsResponse {
  transactions: Transaction[]
  total_count: number
  limit: number
  offset: number
  has_more: boolean
  filters_applied: Record<string, any>
}

export interface TransactionSummary {
  period: string
  start_date?: string
  end_date?: string
  totals: {
    income: number
    expenses: number
    net: number
    transaction_count: number
  }
  by_bank: Record<SourceBank, {
    income: number
    expenses: number
    net: number
    transaction_count: number
  }>
  top_categories: Array<{
    category: string
    amount: number
    transaction_count: number
    percentage: number
  }>
}

export interface CategoryBreakdown {
  period: string
  start_date?: string
  end_date?: string
  total_expenses: number
  categories: Array<{
    category: string
    subcategories: Array<{
      subcategory: string
      amount: number
      transaction_count: number
      percentage_of_category: number
    }>
    total_amount: number
    transaction_count: number
    percentage_of_total: number
  }>
}

export interface MerchantSpending {
  period: string
  start_date?: string
  end_date?: string
  total_count: number
  merchants: Array<{
    merchant_id: string
    merchant_name: string
    category: string
    total_amount: number
    transaction_count: number
    is_subscription: boolean
    percentage_of_total: number
  }>
  limit: number
}

export interface MonthlyTrend {
  range: {
    start_date: string
    end_date: string
  }
  months: Array<{
    month: string
    year: number
    income: number
    expenses: number
    net: number
    transaction_count: number
  }>
}

export interface Balance {
  source_bank: SourceBank
  name: string
  type: "checking" | "credit_card"
  balance: number
  breakdown: {
    total_income?: number
    total_expenses?: number
    total_charges?: number
    total_payments?: number
  }
  last_transaction_date?: string
}

export interface BalanceSummary {
  as_of_date: string
  accounts: Record<SourceBank, Balance>
  summary: {
    total_cash: number
    total_debt: number
    net_worth: number
  }
}

export interface MerchantsListResponse {
  merchants: MerchantDetails[]
  total_count: number
  limit: number
}

export interface MerchantDetailsResponse extends MerchantDetails {
  statistics?: {
    total_transactions: number
    total_spent: number
    avg_transaction: number
    first_transaction_date: string
    last_transaction_date: string
  }
}

export interface CategoriesResponse {
  categories: Array<{
    category: string
    subcategories: string[]
    transaction_count: number
    total_amount: number
    percentage_of_total: number
  }>
  total_expenses: number
  period: string
  start_date?: string
  end_date?: string
}

// Query Parameters
export interface TransactionFilters {
  type?: TransactionType
  category?: string
  source_bank?: SourceBank
  merchant?: string
  is_recurring?: boolean
  tags?: string
  period?: DatePeriod
  start_date?: string
  end_date?: string
  min_amount?: number
  max_amount?: number
  limit?: number
  offset?: number
  sort?: "date" | "amount"
  order?: "asc" | "desc"
}

export interface MerchantFilters {
  category?: string
  is_subscription?: boolean
  limit?: number
}
