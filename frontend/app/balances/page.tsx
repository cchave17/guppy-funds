"use client"

import { useAllBalances } from "@/hooks/use-balances"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { formatCurrency, formatDate } from "@/lib/utils"
import { Wallet, CreditCard, TrendingUp, TrendingDown } from "lucide-react"

export default function BalancesPage() {
  const { data: balances, isLoading } = useAllBalances()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-muted-foreground">Loading balances...</div>
      </div>
    )
  }

  if (!balances) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-muted-foreground">No balance data available</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Account Balances</h2>
        <p className="text-muted-foreground">
          Overview of your accounts and net worth
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Cash</CardTitle>
            <Wallet className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(balances.summary.total_cash)}
            </div>
            <p className="text-xs text-muted-foreground">Checking accounts</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Debt</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {formatCurrency(balances.summary.total_debt)}
            </div>
            <p className="text-xs text-muted-foreground">Credit card balances</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Net Worth</CardTitle>
            {balances.summary.net_worth >= 0 ? (
              <TrendingUp className="h-4 w-4 text-green-600" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-600" />
            )}
          </CardHeader>
          <CardContent>
            <div
              className={`text-2xl font-bold ${
                balances.summary.net_worth >= 0
                  ? "text-green-600"
                  : "text-red-600"
              }`}
            >
              {formatCurrency(balances.summary.net_worth)}
            </div>
            <p className="text-xs text-muted-foreground">
              As of {formatDate(balances.as_of_date)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Account Details */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Object.entries(balances.accounts).map(([bank, account]) => (
          <Card key={bank}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{account.name}</CardTitle>
                <Badge variant={account.type === "checking" ? "default" : "secondary"}>
                  {account.type === "checking" ? "Checking" : "Credit Card"}
                </Badge>
              </div>
              <CardDescription className="uppercase">{bank}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="text-sm text-muted-foreground mb-1">
                  Current Balance
                </div>
                <div
                  className={`text-3xl font-bold ${
                    account.type === "checking"
                      ? account.balance >= 0
                        ? "text-green-600"
                        : "text-red-600"
                      : account.balance >= 0
                      ? "text-red-600"
                      : "text-green-600"
                  }`}
                >
                  {formatCurrency(account.balance)}
                </div>
              </div>

              <div className="space-y-2 pt-4 border-t">
                {account.type === "checking" ? (
                  <>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Total Income:</span>
                      <span className="font-medium text-green-600">
                        {formatCurrency(account.breakdown.total_income || 0)}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Total Expenses:</span>
                      <span className="font-medium text-red-600">
                        {formatCurrency(account.breakdown.total_expenses || 0)}
                      </span>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Total Charges:</span>
                      <span className="font-medium text-red-600">
                        {formatCurrency(account.breakdown.total_charges || 0)}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Total Payments:</span>
                      <span className="font-medium text-green-600">
                        {formatCurrency(account.breakdown.total_payments || 0)}
                      </span>
                    </div>
                  </>
                )}
              </div>

              {account.last_transaction_date && (
                <div className="text-xs text-muted-foreground pt-2 border-t">
                  Last transaction: {formatDate(account.last_transaction_date)}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
