"use client"

import { useState } from "react"
import { useMerchants } from "@/hooks/use-merchants"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { formatCurrency } from "@/lib/utils"
import { Store, Tag, TrendingUp } from "lucide-react"
import type { MerchantFilters } from "@/lib/types"

export default function MerchantsPage() {
  const [filters, setFilters] = useState<MerchantFilters>({
    limit: 50,
  })

  const { data, isLoading } = useMerchants(filters)

  const handleFilterChange = (key: keyof MerchantFilters, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Merchants</h2>
        <p className="text-muted-foreground">
          Browse all merchants and their categories
        </p>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <Input
                id="category"
                placeholder="Filter by category..."
                value={filters.category || ""}
                onChange={(e) =>
                  handleFilterChange("category", e.target.value || undefined)
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="subscription">Type</Label>
              <select
                id="subscription"
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                value={
                  filters.is_subscription === undefined
                    ? ""
                    : filters.is_subscription.toString()
                }
                onChange={(e) =>
                  handleFilterChange(
                    "is_subscription",
                    e.target.value === "" ? undefined : e.target.value === "true"
                  )
                }
              >
                <option value="">All Merchants</option>
                <option value="true">Subscriptions Only</option>
                <option value="false">Non-Subscriptions Only</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Merchants Grid */}
      <div>
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="text-muted-foreground">Loading merchants...</div>
          </div>
        ) : data && data.merchants.length > 0 ? (
          <>
            <div className="mb-4 text-sm text-muted-foreground">
              Showing {data.merchants.length} of {data.total_count} merchants
            </div>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {data.merchants.map((merchant) => (
                <Card key={merchant.merchant_id}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <Store className="h-5 w-5 text-muted-foreground" />
                        <CardTitle className="text-lg">{merchant.name}</CardTitle>
                      </div>
                      {merchant.is_subscription && (
                        <Badge variant="default">Subscription</Badge>
                      )}
                    </div>
                    <CardDescription>
                      {merchant.category}
                      {merchant.subcategory && ` - ${merchant.subcategory}`}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {merchant.tags.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {merchant.tags.map((tag) => (
                          <Badge key={tag} variant="outline" className="text-xs">
                            <Tag className="h-3 w-3 mr-1" />
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    )}

                    {merchant.aliases.length > 0 && (
                      <div>
                        <div className="text-xs text-muted-foreground mb-1">
                          Also known as:
                        </div>
                        <div className="text-xs">
                          {merchant.aliases.slice(0, 3).join(", ")}
                          {merchant.aliases.length > 3 && "..."}
                        </div>
                      </div>
                    )}

                    {merchant.location && (
                      <div className="text-xs text-muted-foreground">
                        {merchant.location.city && merchant.location.state && (
                          <div>
                            {merchant.location.city}, {merchant.location.state}
                          </div>
                        )}
                      </div>
                    )}

                    <div className="pt-4 border-t">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">
                          Confidence:
                        </span>
                        <span className="font-medium">
                          {(merchant.enrichment_confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-32 text-muted-foreground">
            No merchants found
          </div>
        )}
      </div>
    </div>
  )
}
