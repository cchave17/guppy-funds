"use client"

import { Fish } from "lucide-react"
import { useAllBalances } from "@/hooks/use-balances"
import { formatCurrency } from "@/lib/utils"

export function Header() {
  const { data: balances } = useAllBalances()

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center px-4">
        <div className="mr-4 flex items-center gap-2">
          <Fish className="h-6 w-6 text-primary" />
          <h1 className="text-xl font-bold">Guppy Funds</h1>
        </div>

        <div className="flex-1" />

        {balances && (
          <div className="flex items-center gap-6 text-sm">
            <div>
              <span className="text-muted-foreground">Net Worth: </span>
              <span
                className={cn(
                  "font-semibold",
                  balances.summary.net_worth >= 0
                    ? "text-green-600 dark:text-green-400"
                    : "text-red-600 dark:text-red-400"
                )}
              >
                {formatCurrency(balances.summary.net_worth)}
              </span>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}

function cn(...classes: (string | undefined | false)[]) {
  return classes.filter(Boolean).join(" ")
}
