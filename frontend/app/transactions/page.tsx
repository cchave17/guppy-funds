"use client"

import { useState } from "react"
import { useTransactions } from "@/hooks/use-transactions"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { formatCurrency, formatDate } from "@/lib/utils"
import type { TransactionFilters } from "@/lib/types"
import { Search, Filter, ChevronLeft, ChevronRight } from "lucide-react"

export default function TransactionsPage() {
  const [filters, setFilters] = useState<TransactionFilters>({
    limit: 50,
    offset: 0,
    sort: "date",
    order: "desc",
  })

  const [searchTerm, setSearchTerm] = useState("")
  const { data, isLoading } = useTransactions(filters)

  const handleFilterChange = (key: keyof TransactionFilters, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value, offset: 0 }))
  }

  const handleNextPage = () => {
    setFilters((prev) => ({
      ...prev,
      offset: (prev.offset || 0) + (prev.limit || 50),
    }))
  }

  const handlePrevPage = () => {
    setFilters((prev) => ({
      ...prev,
      offset: Math.max(0, (prev.offset || 0) - (prev.limit || 50)),
    }))
  }

  const handleSearch = () => {
    if (searchTerm) {
      handleFilterChange("merchant", searchTerm)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Transactions</h2>
        <p className="text-muted-foreground">
          View and filter all your transactions
        </p>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>Filter transactions by various criteria</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="merchant">Merchant Search</Label>
              <div className="flex gap-2">
                <Input
                  id="merchant"
                  placeholder="Search merchant..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                />
                <Button onClick={handleSearch} size="icon">
                  <Search className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="type">Transaction Type</Label>
              <select
                id="type"
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                value={filters.type || ""}
                onChange={(e) =>
                  handleFilterChange("type", e.target.value || undefined)
                }
              >
                <option value="">All Types</option>
                <option value="income">Income</option>
                <option value="debit">Debit</option>
                <option value="credit">Credit</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="bank">Source Bank</Label>
              <select
                id="bank"
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                value={filters.source_bank || ""}
                onChange={(e) =>
                  handleFilterChange("source_bank", e.target.value || undefined)
                }
              >
                <option value="">All Banks</option>
                <option value="amex">AMEX</option>
                <option value="citi">Citi</option>
                <option value="wells">Wells Fargo</option>
              </select>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="period">Period</Label>
              <select
                id="period"
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                value={filters.period || ""}
                onChange={(e) =>
                  handleFilterChange("period", e.target.value || undefined)
                }
              >
                <option value="">All Time</option>
                <option value="current_month">Current Month</option>
                <option value="last_30_days">Last 30 Days</option>
                <option value="ytd">Year to Date</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="recurring">Recurring</Label>
              <select
                id="recurring"
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                value={filters.is_recurring === undefined ? "" : filters.is_recurring.toString()}
                onChange={(e) =>
                  handleFilterChange(
                    "is_recurring",
                    e.target.value === "" ? undefined : e.target.value === "true"
                  )
                }
              >
                <option value="">All</option>
                <option value="true">Recurring Only</option>
                <option value="false">Non-Recurring Only</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label>Actions</Label>
              <Button
                variant="outline"
                className="w-full"
                onClick={() => {
                  setFilters({ limit: 50, offset: 0, sort: "date", order: "desc" })
                  setSearchTerm("")
                }}
              >
                <Filter className="mr-2 h-4 w-4" />
                Clear Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Transactions Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            {data ? `${data.total_count} Transactions` : "Transactions"}
          </CardTitle>
          <CardDescription>
            {data && `Showing ${data.offset + 1}-${Math.min(data.offset + data.limit, data.total_count)} of ${data.total_count}`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-muted-foreground">Loading transactions...</div>
            </div>
          ) : data && data.transactions.length > 0 ? (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Merchant</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Bank</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.transactions.map((tx) => (
                    <TableRow key={tx.transaction_id}>
                      <TableCell className="font-medium">
                        {formatDate(tx.date)}
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{tx.merchant.name}</div>
                          {tx.is_recurring && (
                            <Badge variant="outline" className="mt-1 text-xs">
                              Recurring
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{tx.merchant.category}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">
                          {tx.source_bank.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            tx.type === "income"
                              ? "default"
                              : tx.type === "debit"
                              ? "destructive"
                              : "secondary"
                          }
                        >
                          {tx.type}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <span
                          className={
                            tx.type === "income"
                              ? "text-green-600 font-semibold"
                              : tx.type === "debit"
                              ? "text-red-600 font-semibold"
                              : "font-semibold"
                          }
                        >
                          {tx.type === "income" ? "+" : tx.type === "debit" ? "-" : ""}
                          {formatCurrency(tx.amount)}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              <div className="flex items-center justify-between mt-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handlePrevPage}
                  disabled={!data.offset || data.offset === 0}
                >
                  <ChevronLeft className="h-4 w-4 mr-2" />
                  Previous
                </Button>
                <div className="text-sm text-muted-foreground">
                  Page {Math.floor((data.offset || 0) / (data.limit || 50)) + 1} of{" "}
                  {Math.ceil(data.total_count / (data.limit || 50))}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleNextPage}
                  disabled={!data.has_more}
                >
                  Next
                  <ChevronRight className="h-4 w-4 ml-2" />
                </Button>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-32 text-muted-foreground">
              No transactions found. Try adjusting your filters.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
