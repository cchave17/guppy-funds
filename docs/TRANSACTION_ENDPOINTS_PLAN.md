# Transaction Endpoints Implementation Plan

Complete plan for building transaction query and analytics endpoints.

---

## 🎯 Overview

Build a comprehensive set of GET endpoints to query, filter, and analyze enriched transaction data.

**Design Philosophy:**
- Hybrid approach: Sub-resources for common queries + query params for flexibility
- Default to current month (configurable)
- Pagination with 50 items default
- RESTful and intuitive

---

## 📋 Phase 1: Create OpenAPI/Swagger Documentation ✅ COMPLETE

**Deliverables:**
- ✅ Enhanced FastAPI metadata (title, description)
- ✅ Response models for better Swagger docs
- ✅ OpenAPI schema available at `/openapi.json`
- ✅ Swagger UI at `/docs`
- ✅ ReDoc at `/redoc`
- ✅ Documentation guide (`SWAGGER_GUIDE.md`)

**Access:**
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)
- `swagger_schema.json` file for editor.swagger.io

---

## 📋 Phase 2: Main Transactions Endpoint

**Endpoint:**
```
GET /v1/transactions
```

**Query Parameters:**
- `type`: income|debit|credit
- `category`: Shopping, Restaurants, Income, etc.
- `source_bank`: amex|citi|wells
- `merchant`: merchant name (partial match)
- `is_recurring`: true|false
- `tags`: comma-separated list
- `period`: current_month|last_30_days|ytd|all_time (default: current_month)
- `start_date`: YYYY-MM-DD (custom range)
- `end_date`: YYYY-MM-DD (custom range)
- `min_amount`, `max_amount`: number
- `limit`: number (default: 50, max: 500)
- `offset`: number (default: 0)
- `sort`: date|amount (default: date)
- `order`: asc|desc (default: desc)

**Response:**
```json
{
  "transactions": [...],
  "total_count": 150,
  "limit": 50,
  "offset": 0,
  "has_more": true,
  "filters_applied": {
    "period": "current_month",
    "type": "income"
  }
}
```

**Implementation:**
1. Create response models
2. Build MongoDB query with all filters
3. Handle date period calculations
4. Add pagination
5. Add sorting

**Time Estimate:** 40-50 minutes

---

## 📋 Phase 3: Transaction Aliases

**Endpoints:**
```
GET /v1/transactions/{transaction_id}
GET /v1/transactions/income
GET /v1/transactions/expenses
GET /v1/transactions/subscriptions
```

**What they do:**
- `/income` → `/transactions?type=income`
- `/expenses` → `/transactions?type=debit`
- `/subscriptions` → `/transactions?is_recurring=true`
- `/{id}` → Single transaction lookup

**Response:** Same as main endpoint (but pre-filtered)

**Implementation:**
1. Create wrapper functions
2. Reuse main transaction query logic
3. Add single transaction lookup

**Time Estimate:** 15-20 minutes

---

## 📋 Phase 4: Aggregation Endpoints

### GET /v1/transactions/summary

**Response:**
```json
{
  "period": {
    "start": "2025-10-01",
    "end": "2025-10-31",
    "type": "current_month"
  },
  "totals": {
    "income": 5000.00,
    "expenses": 3500.00,
    "net": 1500.00,
    "transaction_count": 150
  },
  "by_bank": {
    "wells": {
      "income": 4000.00,
      "expenses": 500.00,
      "net": 3500.00,
      "running_balance": 3500.00
    },
    "amex": {
      "expenses": 2000.00,
      "payments": 0.00,
      "amount_owed": -2000.00
    },
    "citi": {
      "expenses": 1000.00,
      "payments": 0.00,
      "amount_owed": -1000.00
    }
  },
  "top_categories": [
    { "category": "Groceries", "total": 800.00, "count": 25 },
    ...
  ]
}
```

### GET /v1/transactions/by-category

**Response:**
```json
{
  "categories": [
    {
      "category": "Groceries",
      "total": 800.00,
      "count": 25,
      "percentage": 22.8,
      "average": 32.00
    },
    ...
  ],
  "period": "current_month"
}
```

### GET /v1/transactions/by-merchant

**Response:**
```json
{
  "merchants": [
    {
      "merchant_name": "Amazon Marketplace",
      "merchant_id": "amazon-marketplace",
      "total": 450.00,
      "count": 12,
      "category": "Shopping",
      "is_subscription": false
    },
    ...
  ],
  "limit": 20
}
```

### GET /v1/transactions/by-month

**Response:**
```json
{
  "months": [
    {
      "month": "2025-10",
      "income": 5000.00,
      "expenses": 3500.00,
      "net": 1500.00,
      "transaction_count": 150
    },
    {
      "month": "2025-09",
      "income": 4800.00,
      "expenses": 3200.00,
      "net": 1600.00,
      "transaction_count": 142
    },
    ...
  ],
  "range": "last_12_months"
}
```

**Implementation:**
1. MongoDB aggregation pipelines
2. Date grouping logic
3. Percentage calculations
4. Top N filtering

**Time Estimate:** 30-40 minutes

---

## 📋 Phase 5: Balances Endpoint

### GET /v1/balances

**Calculation Logic:**

**Wells Fargo (Checking/Debit):**
```
running_balance = SUM(income transactions) - SUM(debit transactions)
```

**AMEX/Citi (Credit Cards):**
```
amount_owed = SUM(debit transactions) - SUM(payment transactions)
```
*Note: Negative number indicates debt*

**Net Worth:**
```
net_worth = Wells balance - (AMEX debt + Citi debt)
```

**Response:**
```json
{
  "as_of_date": "2025-10-28",
  "accounts": {
    "wells": {
      "name": "Wells Fargo Checking",
      "type": "checking",
      "running_balance": 3500.00,
      "income_total": 8000.00,
      "expenses_total": 4500.00
    },
    "amex": {
      "name": "American Express",
      "type": "credit_card",
      "amount_owed": -2000.00,
      "charges": 2000.00,
      "payments": 0.00
    },
    "citi": {
      "name": "Citi Costco Visa",
      "type": "credit_card",
      "amount_owed": -1000.00,
      "charges": 1000.00,
      "payments": 0.00
    }
  },
  "summary": {
    "total_cash": 3500.00,
    "total_debt": -3000.00,
    "net_worth": 500.00
  }
}
```

### GET /v1/balances/{source_bank}

**Response:**
```json
{
  "source_bank": "wells",
  "running_balance": 3500.00,
  "breakdown": {
    "income": 8000.00,
    "expenses": 4500.00,
    "net": 3500.00
  },
  "last_transaction_date": "2025-10-27"
}
```

**Implementation:**
1. Aggregate income by bank
2. Aggregate expenses by bank
3. Calculate balances
4. Handle credit vs debit accounts differently

**Time Estimate:** 25-30 minutes

---

## 📋 Phase 6: Merchants & Categories Endpoints

### GET /v1/merchants

**Query Params:**
- `category`: filter by category
- `is_subscription`: true|false
- `limit`: default 50

**Response:**
```json
{
  "merchants": [
    {
      "merchant_id": "amazon-marketplace",
      "name": "Amazon Marketplace",
      "category": "Shopping",
      "subcategory": "Online Retail",
      "is_subscription": false,
      "transaction_count": 12,
      "total_spent": 567.89,
      "aliases": ["AMAZON MARKETPLACE NA", "AMZN.COM"]
    },
    ...
  ],
  "total_count": 65
}
```

### GET /v1/merchants/{merchant_id}

**Response:**
```json
{
  "merchant_id": "amazon-marketplace",
  "name": "Amazon Marketplace",
  "category": "Shopping",
  "subcategory": "Online Retail",
  "is_subscription": false,
  "statistics": {
    "transaction_count": 12,
    "total_spent": 567.89,
    "average_transaction": 47.32,
    "first_transaction": "2025-09-15",
    "last_transaction": "2025-10-25"
  },
  "recent_transactions": [...]
}
```

### GET /v1/merchants/{merchant_id}/transactions

Same as `/v1/transactions?merchant={name}` but uses merchant_id

### GET /v1/categories

**Response:**
```json
{
  "categories": [
    {
      "category": "Groceries",
      "total": 800.00,
      "count": 25,
      "percentage": 22.8,
      "subcategories": [
        { "name": "Supermarket", "total": 600.00, "count": 18 },
        { "name": "Convenience Store", "total": 200.00, "count": 7 }
      ]
    },
    ...
  ],
  "period": "current_month",
  "total_expenses": 3500.00
}
```

### GET /v1/tags (Optional)

**Response:**
```json
{
  "tags": [
    { "tag": "amazon", "count": 12, "total": 567.89 },
    { "tag": "grocery", "count": 25, "total": 800.00 },
    ...
  ]
}
```

**Implementation:**
1. Query merchants collection
2. Aggregate transaction data
3. Calculate statistics
4. Join with transaction counts

**Time Estimate:** 30-35 minutes

---

## 🎯 Complete Implementation Summary

### Timeline

| Phase | Description | Time | Dependencies |
|-------|-------------|------|--------------|
| **Phase 1** ✅ | Swagger docs | 15 min | None |
| **Phase 2** | Main transactions endpoint | 45 min | None |
| **Phase 3** | Transaction aliases | 20 min | Phase 2 |
| **Phase 4** | Aggregations (summary, grouping) | 35 min | Phase 2 |
| **Phase 5** | Balances | 30 min | Phase 2 |
| **Phase 6** | Merchants & categories | 35 min | None |

**Total Estimated Time:** ~3 hours

---

## 🔧 Technical Details

### Date Period Helper

```python
def get_date_range(period: str) -> tuple[datetime, datetime]:
    today = datetime.utcnow()

    if period == "current_month":
        start = today.replace(day=1, hour=0, minute=0, second=0)
        end = today

    elif period == "last_30_days":
        start = today - timedelta(days=30)
        end = today

    elif period == "ytd":
        start = today.replace(month=1, day=1, hour=0, minute=0, second=0)
        end = today

    elif period == "all_time":
        start = datetime(2000, 1, 1)
        end = today

    return start, end
```

### MongoDB Aggregation Pattern

```python
pipeline = [
    {"$match": filters},
    {"$group": {
        "_id": "$merchant.category",
        "total": {"$sum": "$amount"},
        "count": {"$sum": 1}
    }},
    {"$sort": {"total": -1}},
    {"$limit": limit}
]
```

---

## ✅ Success Criteria

**Phase 2 Complete When:**
- Can query transactions with any combination of filters
- Pagination works
- Period filtering works (current_month, last_30_days, ytd, all_time)
- Custom date ranges work

**Phase 4 Complete When:**
- `/summary` returns accurate totals by bank
- Balance calculations correct for checking vs credit
- Category grouping shows spending breakdown

**Phase 5 Complete When:**
- Wells balance = income - expenses
- AMEX/Citi show debt owed (negative)
- Net worth calculation correct

---

## 🎨 Swagger Documentation

After implementation, the Swagger UI will show:

**Organized by Tags:**
- Import Management (existing)
- Transactions (new)
- Balances (new)
- Merchants (new)
- Categories & Analytics (new)

**Each endpoint will have:**
- Description and usage examples
- Request parameters with validation
- Response schemas with examples
- Try-it-out functionality

---

## 🚀 Next Steps

1. ✅ **Phase 1 COMPLETE** - View Swagger at http://localhost:8000/docs
2. **Review Plan** - Confirm endpoint design
3. **Implement Phase 2** - Core transactions query
4. **Iterate** - Build remaining phases
5. **Test** - Verify all endpoints work with real data

---

## 📝 Notes

**Balance Calculations:**
- Wells Fargo = Checking account → running total (income - expenses)
- AMEX/Citi = Credit cards → amount owed (charges - payments)
- Payments to credit cards should be detected (e.g., "AMERICAN EXPRESS ACH PMT")

**Performance:**
- MongoDB indexes already in place (from docs)
- Aggregation pipelines efficient
- Merchant caching reduces repeated lookups
- Pagination prevents large responses

**Future Enhancements:**
- GraphQL endpoint (if needed)
- WebSocket for real-time updates
- Bulk export (CSV, JSON)
- Custom date grouping (weekly, quarterly)

---

**Ready to proceed with Phase 2?** Review the plan and let me know if you want any changes!
