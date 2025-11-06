"use client"

import { StatCard } from "@/components/dashboard/stat-card"
import { SpendingChart } from "@/components/charts/spending-chart"
import { CategoryChart } from "@/components/charts/category-chart"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { useTransactionSummary, useTransactionsByMonth, useTransactionsByCategory, useTransactions } from "@/hooks/use-transactions"
import { useAllBalances } from "@/hooks/use-balances"
import { DollarSign, TrendingUp, TrendingDown, Wallet, Receipt, ArrowRight } from "lucide-react"
import { formatCurrency, formatDate } from "@/lib/utils"
import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function DashboardPage() {
  const { data: summary, isLoading: summaryLoading } = useTransactionSummary("current_month")
  const { data: balances, isLoading: balancesLoading } = useAllBalances()
  const { data: monthlyData, isLoading: monthlyLoading } = useTransactionsByMonth()
  const { data: categoryData, isLoading: categoryLoading } = useTransactionsByCategory("current_month", undefined, undefined, 6)
  const { data: recentTransactions, isLoading: transactionsLoading } = useTransactions({ limit: 5, sort: "date", order: "desc" })

  const isLoading = summaryLoading || balancesLoading || monthlyLoading || categoryLoading

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-muted-foreground">Loading dashboard...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Overview of your financial activity
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Net Worth"
          value={balances?.summary.net_worth || 0}
          icon={Wallet}
          format="currency"
        />
        <StatCard
          title="Income This Month"
          value={summary?.totals.income || 0}
          icon={TrendingUp}
          format="currency"
        />
        <StatCard
          title="Expenses This Month"
          value={summary?.totals.expenses || 0}
          icon={TrendingDown}
          format="currency"
        />
        <StatCard
          title="Net This Month"
          value={summary?.totals.net || 0}
          icon={DollarSign}
          format="currency"
        />
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Monthly Trends</CardTitle>
            <CardDescription>Income vs Expenses over time</CardDescription>
          </CardHeader>
          <CardContent>
            {monthlyData && monthlyData.months.length > 0 ? (
              <SpendingChart
                data={monthlyData.months.map((m) => ({
                  month: `${m.month.substring(0, 3)} ${m.year}`,
                  income: m.income,
                  expenses: m.expenses,
                  net: m.net,
                }))}
              />
            ) : (
              <div className="flex items-center justify-center h-[350px] text-muted-foreground">
                No data available
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Spending by Category</CardTitle>
            <CardDescription>This month's expense breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            {categoryData && categoryData.categories.length > 0 ? (
              <CategoryChart
                data={categoryData.categories.slice(0, 6).map((c) => ({
                  category: c.category,
                  amount: c.total_amount,
                  percentage: c.percentage_of_total,
                }))}
              />
            ) : (
              <div className="flex items-center justify-center h-[350px] text-muted-foreground">
                No data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Transactions */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Recent Transactions</CardTitle>
            <CardDescription>Your latest 5 transactions</CardDescription>
          </div>
          <Link href="/transactions">
            <Button variant="ghost" size="sm">
              View All
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          {recentTransactions && recentTransactions.transactions.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Merchant</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentTransactions.transactions.map((tx) => (
                  <TableRow key={tx.transaction_id}>
                    <TableCell className="font-medium">
                      {formatDate(tx.date)}
                    </TableCell>
                    <TableCell>{tx.merchant.name}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{tx.merchant.category}</Badge>
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
                            ? "text-green-600"
                            : tx.type === "debit"
                            ? "text-red-600"
                            : ""
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
          ) : (
            <div className="flex items-center justify-center h-32 text-muted-foreground">
              No transactions yet. Import your first CSV to get started!
            </div>
          )}
        </CardContent>
      </Card>

      {/* Top Categories */}
      {summary && summary.top_categories.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Top Spending Categories</CardTitle>
            <CardDescription>This month</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {summary.top_categories.map((cat) => (
                <div key={cat.category} className="flex items-center">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">{cat.category}</span>
                      <span className="text-sm text-muted-foreground">
                        {formatCurrency(cat.amount)} ({cat.percentage.toFixed(1)}%)
                      </span>
                    </div>
                    <div className="w-full bg-secondary rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full transition-all"
                        style={{ width: `${cat.percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
