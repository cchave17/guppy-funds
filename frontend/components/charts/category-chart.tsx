"use client"

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts"
import { formatCurrency } from "@/lib/utils"

interface CategoryChartProps {
  data: Array<{
    category: string
    amount: number
    percentage: number
  }>
}

const COLORS = [
  "hsl(221 83% 53%)",
  "hsl(142 76% 36%)",
  "hsl(0 84% 60%)",
  "hsl(47 96% 53%)",
  "hsl(280 65% 60%)",
  "hsl(24 90% 50%)",
  "hsl(180 65% 50%)",
  "hsl(330 75% 55%)",
]

export function CategoryChart({ data }: CategoryChartProps) {
  return (
    <ResponsiveContainer width="100%" height={350}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ category, percentage }) =>
            `${category}: ${percentage.toFixed(1)}%`
          }
          outerRadius={100}
          fill="#8884d8"
          dataKey="amount"
        >
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          content={({ active, payload }) => {
            if (active && payload && payload.length) {
              return (
                <div className="rounded-lg border bg-background p-3 shadow-sm">
                  <p className="text-sm font-medium">{payload[0].payload.category}</p>
                  <p className="text-sm text-muted-foreground">
                    {formatCurrency(payload[0].payload.amount)}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {payload[0].payload.percentage.toFixed(1)}% of total
                  </p>
                </div>
              )
            }
            return null
          }}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )
}
