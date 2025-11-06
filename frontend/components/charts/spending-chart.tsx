"use client"

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts"
import { formatCurrency } from "@/lib/utils"

interface SpendingChartProps {
  data: Array<{
    month: string
    income: number
    expenses: number
    net: number
  }>
}

export function SpendingChart({ data }: SpendingChartProps) {
  return (
    <ResponsiveContainer width="100%" height={350}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis
          dataKey="month"
          className="text-xs"
          tick={{ fill: "hsl(var(--muted-foreground))" }}
        />
        <YAxis
          className="text-xs"
          tick={{ fill: "hsl(var(--muted-foreground))" }}
          tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
        />
        <Tooltip
          content={({ active, payload }) => {
            if (active && payload && payload.length) {
              return (
                <div className="rounded-lg border bg-background p-3 shadow-sm">
                  <p className="text-sm font-medium">{payload[0].payload.month}</p>
                  <div className="mt-2 space-y-1">
                    <p className="text-sm text-green-600">
                      Income: {formatCurrency(payload[0].payload.income)}
                    </p>
                    <p className="text-sm text-red-600">
                      Expenses: {formatCurrency(payload[0].payload.expenses)}
                    </p>
                    <p className="text-sm font-medium">
                      Net: {formatCurrency(payload[0].payload.net)}
                    </p>
                  </div>
                </div>
              )
            }
            return null
          }}
        />
        <Legend />
        <Bar
          dataKey="income"
          fill="hsl(142 76% 36%)"
          radius={[4, 4, 0, 0]}
          name="Income"
        />
        <Bar
          dataKey="expenses"
          fill="hsl(0 84% 60%)"
          radius={[4, 4, 0, 0]}
          name="Expenses"
        />
      </BarChart>
    </ResponsiveContainer>
  )
}
