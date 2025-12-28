# Developer Onboarding Guide - Guppy Funds

Welcome to Guppy Funds! This guide will help you understand and start contributing to the codebase. Whether you're taking over the project or collaborating, this document provides a structured path to becoming productive.

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Architecture Deep Dive](#architecture-deep-dive)
4. [Code Walkthrough](#code-walkthrough)
5. [Development Workflow](#development-workflow)
6. [Key Design Decisions](#key-design-decisions)
7. [Common Tasks](#common-tasks)
8. [Troubleshooting](#troubleshooting)
9. [Additional Resources](#additional-resources)

---

## Overview

**Guppy Funds** is a personal finance management system that automatically imports, processes, and enriches financial transactions from multiple banks (AMEX, Citi, Wells Fargo) using AI-powered categorization and merchant normalization.

### What Makes This System Unique

- **Automated Processing**: Background worker handles everything after upload
- **AI-Powered Enrichment**: Claude API normalizes merchants and categorizes spending
- **Intelligent Caching**: Merchant data is cached to reduce API costs by ~95%
- **Smart Deduplication**: Prevents duplicate transactions across multiple uploads
- **Real-Time Updates**: Frontend polls for progress and updates live

### Tech Stack at a Glance

**Backend:**
- FastAPI (Python async web framework)
- MongoDB (document database)
- Claude API (AI enrichment)
- Motor (async MongoDB driver)

**Frontend:**
- Next.js 14 (React framework with App Router)
- TypeScript (type safety)
- Tailwind CSS (styling)
- React Query (server state management)
- Recharts (data visualization)

---

## Getting Started

### Phase 1: Get It Running (30 minutes)

**Goal:** See the application in action before diving into code.

#### Step 1: Prerequisites Check

```bash
# Verify you have these installed
docker --version          # Docker 20+
docker-compose --version  # Docker Compose 2+
node --version           # Node.js 18+
```

You'll also need:
- MongoDB Atlas account (or use local MongoDB via Docker)
- Anthropic API key for Claude

#### Step 2: Clone and Configure

```bash
# Clone the repository
git clone <repo-url>
cd guppy-funds

# Set up environment
cp .env.example .env

# Edit .env and add your credentials:
# - MONGODB_URL (MongoDB Atlas connection string)
# - ANTHROPIC_API_KEY (Claude API key)
nano .env
```

#### Step 3: Start Services

```bash
# Start all services (API, Worker, MongoDB, Frontend)
docker-compose up -d

# Verify services are healthy
curl http://localhost:8000/health   # Backend
curl http://localhost:3000          # Frontend
```

#### Step 4: Explore the Live System

1. **Open the Frontend:** http://localhost:3000
   - Browse the dashboard
   - Check out transactions, balances, merchants pages
   - Note: Data will be empty until you upload a CSV

2. **Open Swagger Docs:** http://localhost:8000/docs
   - Interactive API documentation
   - Try the "Try it out" feature on endpoints
   - See request/response schemas

3. **Upload a Sample CSV:**
   ```bash
   # Check if test files exist
   ls test_files/

   # Upload using Swagger UI or curl:
   curl -X POST http://localhost:8000/v1/imports \
     -F "file=@test_files/sample_amex.csv" \
     -F "source_bank=amex"
   ```

4. **Watch the Magic Happen:**
   - Check worker logs: `docker logs guppy-funds-worker -f`
   - Refresh frontend to see transactions appear
   - Open MongoDB Compass and connect to see data flowing through collections

#### Step 5: Explore the Database

**Connect MongoDB Compass:**
- Connection String: (use your MONGODB_URL from .env)
- Database: `guppy_funds`

**Key Collections:**
- `imports` - Import job tracking (see state transitions)
- `transactions_raw` - Original CSV data (immutable)
- `transactions_enriched` - AI-enriched, normalized transactions
- `merchants` - Cached merchant enrichment data

**Try these queries:**
```javascript
// See latest imports
db.imports.find().sort({upload_time: -1}).limit(10)

// See enriched transactions
db.transactions_enriched.find().sort({date: -1}).limit(10)

// See cached merchants
db.merchants.find()
```

---

## Architecture Deep Dive

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                         │
└─────────────────────────────────────────────────────────────────┘
                                  │
                          Upload CSV File
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js)                           │
│                      localhost:3000                              │
│                                                                   │
│  • Dashboard with charts and analytics                           │
│  • Transaction filtering and search                              │
│  • CSV upload wizard                                             │
│  • Real-time progress tracking (React Query polling)             │
└─────────────────────────────────────────────────────────────────┘
                                  │
                           HTTP/REST API
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND API (FastAPI)                         │
│                      localhost:8000                              │
│                                                                   │
│  • File upload endpoint (POST /v1/imports)                       │
│  • Transaction query endpoints (GET /v1/transactions)            │
│  • Balance aggregation (GET /v1/balances)                        │
│  • Merchant management (GET /v1/merchants)                       │
│  • Import status tracking (GET /v1/imports/{id})                 │
└─────────────────────────────────────────────────────────────────┘
                                  │
                        Writes to MongoDB
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MONGODB (Database)                            │
│                     localhost:27017                              │
│                                                                   │
│  Collections:                                                     │
│  • imports           - Job tracking (uploaded → completed)       │
│  • transactions_raw  - Original CSV data (immutable)             │
│  • transactions_enriched - AI-enriched transactions              │
│  • merchants         - Cached enrichment data                    │
└─────────────────────────────────────────────────────────────────┘
                                  ▲
                                  │
                          Polling Every 5s
                                  │
┌─────────────────────────────────────────────────────────────────┐
│                   WORKER (Background Process)                    │
│                                                                   │
│  Infinite loop that:                                             │
│  1. Claims next job (atomic operation)                           │
│  2. Parses CSV → transactions_raw                                │
│  3. Enriches via Claude API → transactions_enriched              │
│  4. Updates job state → completed                                │
│                                                                   │
│  Key Features:                                                    │
│  • Atomic job claiming (prevents duplicate processing)           │
│  • Batch enrichment (up to 50 transactions per API call)         │
│  • Merchant caching (reuses enrichment, saves $$$)               │
│  • Graceful failure handling (partial success allowed)           │
└─────────────────────────────────────────────────────────────────┘
                                  │
                         Calls Claude API
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CLAUDE API (Anthropic)                        │
│                                                                   │
│  Input: Raw merchant names from CSVs                             │
│  Output: Normalized merchant data                                │
│    • Cleaned merchant name                                       │
│    • Category & subcategory                                      │
│    • Tags (e.g., "online", "subscription")                       │
│    • Location data                                               │
│    • Recurring/subscription detection                            │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow: CSV Upload to Enriched Transactions

```
1. User uploads CSV
   └─> API validates file and creates import record (state: "uploaded")

2. Worker picks up job
   └─> Claims job atomically (prevents duplicate processing)

3. PARSING PHASE
   └─> Parser reads CSV (AMEX/Citi/Wells have different formats)
   └─> Checks for duplicates using:
       • AMEX: Reference field (unique transaction ID)
       • Citi/Wells: Fingerprint hash (date+amount+description)
   └─> Inserts into transactions_raw collection
   └─> Updates import state: "parsed"

4. ENRICHMENT PHASE
   └─> Loads transactions_raw for this import
   └─> For each transaction:
       • Check merchant cache first (fast, free)
       • If not cached: Call Claude API (slow, costs money)
       • Normalize merchant name, assign category/tags
       • Cache result for future use
   └─> Inserts into transactions_enriched collection
   └─> Updates import state: "enriched" → "completed"

5. Frontend displays data
   └─> React Query refetches transactions
   └─> Dashboard updates with new data
```

### Import Job State Machine

Every CSV upload goes through these states:

```
uploaded → parsing → parsed → enriching → enriched → completed
   ↓          ↓         ↓          ↓           ↓
   └──────────┴─────────┴──────────┴───────────┴──────→ failed
```

**State Definitions:**
- **uploaded**: File received, waiting for worker
- **parsing**: CSV being read and inserted into transactions_raw
- **parsed**: All rows stored, ready for enrichment
- **enriching**: Claude API processing transactions
- **enriched**: Enrichment complete, data in transactions_enriched
- **completed**: Fully processed (final success state)
- **failed**: Error occurred (check import.errors or import.notes)

**Key Implementation Detail:** Worker uses atomic `find_one_and_update` to claim jobs, preventing duplicate processing even with multiple worker instances.

---

## Code Walkthrough

This section provides a guided tour through the most important parts of the codebase.

### Backend Tour

#### Entry Point: `app/main.py`

Start here to understand the application setup:

```python
# Key sections to examine:
# Line 20-49: FastAPI app configuration
#   - Title, description, version
#   - Swagger/ReDoc endpoints
#   - Lifespan context manager (startup/shutdown)

# Line 52-58: CORS middleware (allows frontend requests)

# Line 60-64: Router registration
#   - imports.router (CSV upload, job management)
#   - transactions.router (querying enriched data)
#   - balances.router (account balance calculations)
#   - merchants.router (merchant directory)
```

**What to learn:** How FastAPI apps are structured, how routers are organized, where middleware is configured.

#### Upload Flow: `app/api/v1/imports.py`

The journey of a CSV upload:

```python
# Function: upload_import() - Line ~20-90
# 1. File validation (size, extension)
# 2. Generate import_id with timestamp
# 3. Save file to uploads directory
# 4. Calculate checksum
# 5. Create import document in MongoDB (state: "uploaded")
# 6. Return 201 Created with import_id

# Key pattern: The API only receives and registers the file.
# The worker does all the heavy lifting asynchronously.
```

**Important:** The API is intentionally lightweight. It doesn't parse or enrich - just accepts the upload and trusts the worker to handle it.

#### The Heart: `app/worker.py`

The background worker that makes everything automatic:

```python
# Main loop: run() - Line ~100-140
# 1. Poll for jobs every 5 seconds
# 2. Try to claim a parsing job (uploaded state)
# 3. Try to claim an enrichment job (parsed state)
# 4. Sleep and repeat forever

# Job claiming: _claim_job() - Line ~58-70
# Uses atomic find_one_and_update to prevent race conditions:
db.imports.find_one_and_update(
    {"state": state, ...},  # Find job in this state
    {"$set": {"started_at": now}},  # Mark as started
    sort=[("upload_time", 1)]  # Oldest first (FIFO)
)
# This prevents two workers from processing the same job!

# Parsing: _process_parsing() - Line ~142-180
# 1. Load appropriate parser (AMEX/Citi/Wells)
# 2. Parse CSV into list of dicts
# 3. Insert into transactions_raw (with deduplication)
# 4. Update import state to "parsed"

# Enrichment: _process_enrichment() - Line ~182-250
# 1. Load all transactions_raw for this import
# 2. Batch enrich (up to 50 at a time)
# 3. Insert into transactions_enriched
# 4. Update import state to "completed"
```

**Key Insight:** The worker is stateless and can be restarted safely. Jobs resume from their last state.

#### CSV Parsers: `app/parsers/`

Each bank has its own parser due to different CSV formats:

**AMEX Parser (`amex_parser.py`):**
```python
# Line ~30-60: parse() method
# - Reads CSV with headers
# - Uses "Reference" field as unique deduplication key
# - Extracts card member, account number
# - Handles positive/negative amounts

# Deduplication strategy:
dedup_key = row["Reference"]  # AMEX provides unique transaction IDs!
```

**Citi Parser (`citi_parser.py`):**
```python
# Line ~30-70: parse() method
# - Separate Debit/Credit columns (need to merge)
# - Uses MD5 fingerprint for deduplication (no unique ID provided)

# Deduplication strategy:
fingerprint = f"{date}|{amount}|{description}|{member_name}"
dedup_key = hashlib.md5(fingerprint.encode()).hexdigest()
```

**Wells Fargo Parser (`wells_parser.py`):**
```python
# Line ~20-50: parse() method
# - NO HEADERS! Position-based parsing
# - Format: [Date, Amount, Flag1, Flag2, Description]
# - Uses fingerprint like Citi

# Deduplication strategy:
fingerprint = f"{date}|{amount}|{description}"
dedup_key = hashlib.md5(fingerprint.encode()).hexdigest()
```

**Pattern to Remember:** Always check for duplicates before inserting. Query transactions_raw for existing dedup_key.

#### AI Magic: `app/enrichers/claude_enricher.py`

Where the AI enrichment happens:

```python
# Main method: enrich_batch() - Line ~50-150
# 1. Group transactions into batches (up to 50)
# 2. For each transaction:
#    a. Check merchant cache first
#    b. If cached: reuse data (fast, free!)
#    c. If not: add to "needs enrichment" list
# 3. Send batch to Claude API with structured prompt
# 4. Parse JSON response
# 5. Cache new merchant data
# 6. Return enriched transactions

# Cache strategy (critical for cost savings):
# Check cache first:
cached = await db.merchants.find_one({"name": merchant_name})
if cached:
    return cached  # No API call needed!

# After enrichment:
await db.merchants.insert_one(merchant_data)  # Cache for next time
```

**Cost Impact:**
- First upload of 100 transactions: ~$0.02-0.05 (50-70 unique merchants)
- Second upload of 100 transactions: ~$0.001 (most merchants cached)
- Ongoing: 95%+ cache hit rate after initial uploads

#### API Endpoints: `app/api/v1/`

**Transaction Queries (`transactions.py`):**
```python
# Main query endpoint: get_transactions() - Line ~30-100
# Supports extensive filtering:
# - type (debit/credit/income)
# - category, merchant, source_bank
# - date ranges (period shortcuts or custom start/end)
# - amount ranges (min/max)
# - recurring status
# - pagination (limit/offset)
# - sorting (date/amount, asc/desc)

# Convenience shortcuts:
# - /income → get_income() - filters type=income
# - /expenses → get_expenses() - filters type=debit
# - /subscriptions → get_subscriptions() - filters is_recurring=true

# Aggregation endpoints:
# - /summary → Financial overview (income, expenses, net, by bank)
# - /by-category → Spending breakdown by category
# - /by-merchant → Top merchants by total spent
# - /by-month → Monthly trends (last 12 months)
```

**Balance Calculations (`balances.py`):**
```python
# get_balances() - Line ~20-80
# Calculates current balances by aggregating all transactions:

# For checking accounts (Wells):
balance = sum(income) - sum(expenses)

# For credit cards (AMEX/Citi):
amount_owed = sum(charges) - sum(payments)  # Negative = you owe

# Net worth:
net_worth = total_cash - total_debt
```

**Pattern:** All endpoints return Pydantic models (type-safe responses).

### Frontend Tour

#### Entry Point: `frontend/app/layout.tsx`

Root layout for the entire app:

```typescript
// Key elements:
// - TanStack Query provider (React Query)
// - Dark mode support (next-themes)
// - Global navigation (Header component)
// - Font configuration (Geist Sans/Mono)
```

#### Dashboard: `frontend/app/page.tsx`

The main landing page:

```typescript
// Line ~20-40: Uses multiple custom hooks
const { data: summary } = useTransactionSummary("current_month")
const { data: categoryData } = useTransactionsByCategory("current_month")
const { data: recentTransactions } = useTransactions({ limit: 10 })

// Line ~50-120: Layout with cards
// - Summary stats (income, expenses, net worth)
// - Category chart (pie chart)
// - Recent transactions list
// - Quick actions

// Pattern: All data fetching uses React Query hooks (no useEffect!)
```

#### API Client: `frontend/lib/api.ts`

Centralized API communication:

```typescript
// Base configuration:
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// Pattern used throughout:
class ApiClient {
  async getTransactions(filters?: TransactionFilters) {
    const response = await fetch(`${API_BASE_URL}/v1/transactions?${params}`)
    if (!response.ok) throw new Error(...)
    return response.json()
  }
}

// All API calls go through this client
// Makes it easy to add auth, error handling, etc. in one place
```

**Key Principle:** Never call fetch directly in components. Always go through apiClient.

#### React Query Hooks: `frontend/hooks/`

Custom hooks that wrap React Query:

**Example: `useTransactions.ts`**
```typescript
export function useTransactions(filters?: TransactionFilters) {
  return useQuery({
    queryKey: ["transactions", filters],  // Automatic caching by filters
    queryFn: () => apiClient.getTransactions(filters),
    staleTime: 1000 * 60 * 5,  // Consider fresh for 5 minutes
  })
}
```

**The Polling Pattern: `useImportStatus.ts`**
```typescript
export function useImportStatus(importId: string | null) {
  return useQuery({
    queryKey: ["import-status", importId],
    queryFn: () => apiClient.getImportStatus(importId!),
    enabled: !!importId,
    refetchInterval: (query) => {
      const state = query.state.data?.state
      // Stop polling when complete or failed
      if (state === "completed" || state === "failed") {
        return false
      }
      return 2000  // Poll every 2 seconds otherwise
    },
  })
}
```

**This is how real-time progress works!** The frontend polls the backend every 2 seconds until the job finishes.

#### Type Safety: `frontend/lib/types.ts`

All TypeScript types matching backend models:

```typescript
// These match Pydantic models in the backend exactly
export interface TransactionEnriched {
  transaction_id: string
  date: string
  amount: number
  type: "debit" | "credit" | "income"
  merchant: MerchantInfo
  // ... matches app/models/transaction.py
}

// Filter types for API queries
export interface TransactionFilters {
  type?: TransactionType
  category?: string
  start_date?: string
  // ... corresponds to query parameters in transactions.py
}
```

**Best Practice:** When you add a field to the backend model, add it here too. TypeScript will catch mismatches.

#### Upload Flow: `frontend/app/import/page.tsx`

The CSV upload wizard:

```typescript
// Line ~40-80: Upload form with validation
// 1. Select file (validates size, extension)
// 2. Select bank (amex/citi/wells)
// 3. Submit via FormData

// Line ~90-130: Progress tracking
const { data: importStatus } = useImportStatus(importId, true)

// Component automatically polls and displays:
// - Current state (parsing, enriching, etc.)
// - Progress bars (rows parsed, enriched)
// - Errors if any
// - Success message when complete
```

---

## Development Workflow

### Making Your First Change

Let's walk through adding a new transaction filter as a learning exercise.

#### Task: Add "Min Amount" Filter to Transactions Page

**Step 1: Backend - Add Filter Parameter**

Edit `app/api/v1/transactions.py`:

```python
# Find get_transactions() function (around line 30)
# Add new parameter to function signature:
async def get_transactions(
    # ... existing parameters ...
    min_amount: Optional[float] = Query(None, description="Minimum transaction amount"),
):
    # Add to MongoDB query
    query = {}

    # ... existing query building ...

    if min_amount is not None:
        query["amount"] = {"$gte": min_amount}

    # ... rest of function
```

**Step 2: Frontend - Update Types**

Edit `frontend/lib/types.ts`:

```typescript
export interface TransactionFilters {
  // ... existing fields ...
  min_amount?: number  // Add this line
}
```

**Step 3: Frontend - Update API Client**

No changes needed! The `apiClient.getTransactions()` already passes all filter properties.

**Step 4: Frontend - Add UI Component**

Edit `frontend/app/transactions/page.tsx`:

```typescript
// Add state
const [minAmount, setMinAmount] = useState<number>()

// Add input field in the filters section
<input
  type="number"
  placeholder="Min Amount"
  value={minAmount || ""}
  onChange={(e) => setMinAmount(e.target.value ? Number(e.target.value) : undefined)}
/>

// Update the useTransactions call to include the new filter
const { data } = useTransactions({
  // ... existing filters ...
  min_amount: minAmount,
})
```

**Step 5: Test**

```bash
# Restart backend (if not using --reload)
docker-compose restart api

# Frontend should hot-reload automatically
# Open http://localhost:3000/transactions
# Try filtering by minimum amount
```

**Step 6: Verify in Swagger**

- Open http://localhost:8000/docs
- Find `GET /v1/transactions`
- You should see the new `min_amount` parameter
- Test it directly in Swagger UI

### Common Development Tasks

#### Adding a New Bank Parser

1. **Create parser file:** `app/parsers/newbank_parser.py`
2. **Implement parse method:** Follow pattern from `amex_parser.py`
3. **Decide deduplication strategy:** Unique ID field or fingerprint?
4. **Update worker:** Add case in `app/worker.py` to load your parser
5. **Test with sample CSV:** Upload via API and check logs

#### Adding a New Enrichment Field

1. **Update Claude prompt:** `app/enrichers/claude_enricher.py`
   - Add field to JSON schema in prompt
   - Add field to Pydantic model
2. **Update transactions_enriched model:** `app/models/transaction.py`
3. **Update frontend types:** `frontend/lib/types.ts`
4. **Display in UI:** Add to transaction card or detail view

#### Adding a New API Endpoint

1. **Create endpoint function:** In appropriate file under `app/api/v1/`
2. **Define request/response models:** Using Pydantic in `app/models/`
3. **Register router:** Already done if using existing router files
4. **Test in Swagger:** Verify at http://localhost:8000/docs
5. **Add frontend support:**
   - Add method to `apiClient` in `frontend/lib/api.ts`
   - Create React Query hook in `frontend/hooks/`
   - Use in components

### Running Tests Locally

Currently, there are no automated tests (this is a known gap). To test:

1. **Manual API Testing:**
   - Use Swagger UI at http://localhost:8000/docs
   - Use curl or Postman
   - Check MongoDB Compass to verify data

2. **Frontend Testing:**
   - Use browser dev tools
   - Check React Query devtools (included in dev mode)
   - Verify network requests in browser

3. **Integration Testing:**
   - Upload real CSV files
   - Monitor worker logs: `docker logs -f guppy-funds-worker`
   - Verify data flows through all collections

### Debugging Tips

**Backend Issues:**

```bash
# View API logs
docker logs -f guppy-funds-api

# View worker logs (most helpful for enrichment issues)
docker logs -f guppy-funds-worker

# Restart just the API
docker-compose restart api

# Run API locally for better debugging
uvicorn app.main:app --reload
```

**Frontend Issues:**

```bash
# Check browser console for errors
# Frontend runs with hot reload automatically

# View React Query state (in browser):
# - Open http://localhost:3000
# - Check React Query DevTools (floating button in bottom right)

# Restart frontend
docker-compose restart frontend
```

**Database Issues:**

```bash
# Connect with MongoDB Compass
# Connection string from your .env MONGODB_URL

# Or use mongosh:
mongosh "mongodb://admin:admin123@localhost:27017"
use guppy_funds
db.imports.find().pretty()
```

**Worker Not Processing:**

```bash
# Check worker is running
docker ps | grep worker

# View logs for errors
docker logs guppy-funds-worker

# Common issues:
# 1. ANTHROPIC_API_KEY not set or invalid
# 2. MongoDB connection failed
# 3. Job stuck in "started" state (restart worker)
```

---

## Key Design Decisions

Understanding *why* things are built this way will help you make better decisions when extending the system.

### Why MongoDB Instead of PostgreSQL?

**Reason:** Flexible schema for varying CSV formats.

Each bank has a different CSV structure:
- AMEX: 15+ columns with rich metadata
- Citi: 6 columns, separate debit/credit
- Wells: No headers, position-based

Using MongoDB's document model:
- No need to create rigid tables that fit all banks
- Easy to add new banks without migrations
- Can store original CSV data as-is in transactions_raw
- JSON-like structure matches API responses naturally

**Trade-off:** Lose SQL joins and ACID guarantees across collections. Acceptable for this use case (personal finance, single user).

### Why Background Worker Instead of Synchronous Processing?

**Reason:** AI enrichment takes 20-60 seconds for typical uploads.

If we did enrichment synchronously in the API:
- User waits 30-60 seconds for upload request to complete
- API server blocked, can't handle other requests
- Risk of timeout on larger files
- Bad user experience

With background worker:
- API responds immediately (201 Created)
- User can see progress in real-time
- Worker processes in background
- Scalable: Can run multiple workers if needed

**Pattern Used:** Job queue with atomic claiming (prevents duplicate processing).

### Why Merchant Caching?

**Reason:** Cost optimization - reduces Claude API costs by ~95%.

Without caching:
- 100 transactions × $0.0005 per transaction = $0.05 per upload
- Upload monthly statements 12x/year = $0.60/year
- Add multiple cards: $2-3/year per user

With caching:
- First upload: $0.05 (enrich all merchants)
- Subsequent uploads: $0.001 (only new merchants)
- Typical ongoing cost: <$0.10/year total

After a few months, cache hit rate reaches 95%+ because you shop at the same places.

**Implementation:**
```python
# Check cache first
cached = await db.merchants.find_one({"name_normalized": merchant})
if cached:
    return cached  # Free!

# Only call API if not cached
enriched = await claude_api.enrich(merchant)
await db.merchants.insert_one(enriched)  # Cache for next time
```

### Why Fingerprint Deduplication for Citi/Wells?

**Reason:** They don't provide unique transaction IDs.

AMEX gives us a Reference field (unique transaction ID). Easy:
```python
dedup_key = row["Reference"]
```

Citi and Wells don't. We need to create our own identifier:
```python
fingerprint = f"{date}|{amount}|{description}|{member}"
dedup_key = hashlib.md5(fingerprint.encode()).hexdigest()
```

**Trade-off:**
- Pro: Prevents duplicates across uploads
- Con: If you have two identical transactions on the same day for the same amount at the same merchant, we'll treat as duplicate
- Reality: Rare enough to accept this trade-off

### Why React Query for State Management?

**Reason:** Server state is fundamentally different from client state.

Server state characteristics:
- Asynchronously fetched
- Can be stale (needs refetching)
- Shared across components
- Needs caching

React Query handles this automatically:
```typescript
const { data, isLoading, error } = useTransactions()
// Automatically:
// - Caches by query key
// - Refetches on window focus
// - Deduplicates requests
// - Handles loading/error states
```

Without React Query, you'd need to manually:
- Track loading states
- Cache responses
- Handle refetching
- Prevent duplicate requests
- Manage stale data

**Result:** Significantly less boilerplate, better UX.

### Why Next.js 14 App Router?

**Reason:** Modern React patterns with built-in optimizations.

Benefits:
- Server components (faster initial load)
- Automatic code splitting
- Built-in routing (file-based)
- API routes (if we need them)
- Image optimization
- TypeScript support out of the box

**Trade-off:** Learning curve if unfamiliar with React Server Components. But for new projects, it's the recommended approach.

### Why Separate Raw and Enriched Collections?

**Reason:** Immutability and reprocessing capability.

`transactions_raw`:
- Original CSV data (immutable)
- Allows reprocessing if enrichment logic changes
- Audit trail of what was actually imported

`transactions_enriched`:
- Normalized, unified format
- AI-enhanced data
- Can be regenerated from raw at any time

If you improve the enrichment prompt, you can:
```python
# Reprocess all transactions
for raw in db.transactions_raw.find():
    enriched = await enricher.enrich(raw)
    await db.transactions_enriched.insert_one(enriched)
```

**Pattern:** Separate source of truth from computed data.

---

## Common Tasks

### How to Add a New Bank

**Step 1: Create Parser**

```python
# app/parsers/newbank_parser.py
from typing import List, Dict
import csv

class NewBankParser:
    def __init__(self):
        self.bank_name = "newbank"

    def parse(self, file_path: str) -> List[Dict]:
        transactions = []

        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Extract fields from CSV
                transaction = {
                    "date": row["Date"],
                    "description": row["Description"],
                    "amount": float(row["Amount"]),
                    # ... other fields

                    # Deduplication key
                    "dedup_key": self._generate_dedup_key(row),
                }
                transactions.append(transaction)

        return transactions

    def _generate_dedup_key(self, row: Dict) -> str:
        # Option 1: If bank provides unique ID
        return row["TransactionID"]

        # Option 2: Generate fingerprint
        import hashlib
        fingerprint = f"{row['Date']}|{row['Amount']}|{row['Description']}"
        return hashlib.md5(fingerprint.encode()).hexdigest()
```

**Step 2: Register in Worker**

```python
# app/worker.py
from app.parsers.newbank_parser import NewBankParser

# In _process_parsing method, add case:
if import_doc["source_bank"] == "newbank":
    parser = NewBankParser()
```

**Step 3: Update Frontend**

```typescript
// frontend/lib/types.ts
export type SourceBank = "amex" | "citi" | "wells" | "newbank"

// frontend/app/import/page.tsx
// Add option to bank selector
<option value="newbank">New Bank</option>
```

**Step 4: Test**

```bash
curl -X POST http://localhost:8000/v1/imports \
  -F "file=@newbank_sample.csv" \
  -F "source_bank=newbank"
```

### How to Modify the Enrichment Prompt

The enrichment prompt defines what Claude returns:

```python
# app/enrichers/claude_enricher.py

# Find the _build_enrichment_prompt method
def _build_enrichment_prompt(self, transactions: List[Dict]) -> str:
    prompt = """
    You are a financial transaction enrichment system.

    For each transaction, return:
    {
        "merchant_name": "Normalized merchant name",
        "category": "Primary category",
        "subcategory": "More specific category",
        "tags": ["tag1", "tag2"],
        "is_subscription": true/false,
        "location": "City, State (if identifiable)",

        // ADD YOUR NEW FIELD HERE:
        "your_new_field": "description of what this should contain"
    }
    """
    # ... rest of prompt
```

**After changing prompt:**
1. Restart worker: `docker-compose restart worker`
2. Upload a new CSV to test
3. Check MongoDB to verify new field appears

**To reprocess existing data:**
```python
# Write a script to reprocess
for raw in db.transactions_raw.find():
    enriched = await enricher.enrich(raw)
    await db.transactions_enriched.replace_one(
        {"transaction_id": enriched["transaction_id"]},
        enriched,
        upsert=True
    )
```

### How to Add a New Dashboard Chart

**Step 1: Create Data Endpoint (if needed)**

If the data doesn't exist yet:

```python
# app/api/v1/transactions.py
@router.get("/spending-over-time")
async def get_spending_over_time(period: str = "ytd"):
    # Aggregate spending by day/week/month
    pipeline = [
        {"$group": {
            "_id": "$date",
            "total": {"$sum": "$amount"}
        }},
        {"$sort": {"_id": 1}}
    ]
    results = await db.transactions_enriched.aggregate(pipeline).to_list(None)
    return results
```

**Step 2: Add React Query Hook**

```typescript
// frontend/hooks/useSpendingOverTime.ts
export function useSpendingOverTime(period: string = "ytd") {
  return useQuery({
    queryKey: ["spending-over-time", period],
    queryFn: () => apiClient.getSpendingOverTime(period),
  })
}
```

**Step 3: Create Chart Component**

```typescript
// frontend/components/charts/SpendingOverTimeChart.tsx
import { LineChart, Line, XAxis, YAxis } from "recharts"

export function SpendingOverTimeChart({ period }: { period: string }) {
  const { data, isLoading } = useSpendingOverTime(period)

  if (isLoading) return <div>Loading...</div>

  return (
    <LineChart width={600} height={300} data={data}>
      <XAxis dataKey="date" />
      <YAxis />
      <Line type="monotone" dataKey="total" stroke="#8884d8" />
    </LineChart>
  )
}
```

**Step 4: Add to Dashboard**

```typescript
// frontend/app/page.tsx
import { SpendingOverTimeChart } from "@/components/charts/SpendingOverTimeChart"

// In your dashboard layout:
<Card>
  <CardHeader>
    <CardTitle>Spending Trend</CardTitle>
  </CardHeader>
  <CardContent>
    <SpendingOverTimeChart period="ytd" />
  </CardContent>
</Card>
```

### How to Change Claude Model

**Option 1: Via Environment Variable**

```bash
# .env
CLAUDE_MODEL=claude-3-5-sonnet-20241022  # More capable, more expensive
# or
CLAUDE_MODEL=claude-3-5-haiku-20241022   # Faster, cheaper (default)
```

**Option 2: Programmatically**

```python
# app/config.py
class Settings(BaseSettings):
    claude_model: str = Field(
        default="claude-3-5-haiku-20241022",
        env="CLAUDE_MODEL"
    )
```

**Cost Comparison:**
- Haiku: ~$0.0005 per transaction (recommended for production)
- Sonnet: ~$0.002 per transaction (use if you need better categorization)

### How to Export Data

**Quick Export via MongoDB Compass:**
1. Open collection (e.g., transactions_enriched)
2. Click "Export Data"
3. Choose format (JSON/CSV)
4. Save file

**Programmatic Export:**

Add an export endpoint:

```python
# app/api/v1/transactions.py
from fastapi.responses import StreamingResponse
import csv
import io

@router.get("/export")
async def export_transactions(
    format: str = "csv",
    # ... filter parameters ...
):
    # Query transactions
    transactions = await db.transactions_enriched.find(query).to_list(None)

    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[...])
        writer.writeheader()
        writer.writerows(transactions)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=transactions.csv"}
        )
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: Worker Not Processing Uploads

**Symptoms:**
- Upload succeeds (returns 201)
- Import stays in "uploaded" state
- Worker logs show nothing

**Debug Steps:**
```bash
# 1. Check worker is running
docker ps | grep worker

# 2. View worker logs
docker logs guppy-funds-worker -f

# 3. Check import record
# In MongoDB Compass:
db.imports.find().sort({upload_time: -1})
```

**Common Causes:**
- Worker not started: `docker-compose up -d worker`
- Worker crashed: Check logs for Python errors
- MongoDB connection issue: Verify MONGODB_URL in .env
- ANTHROPIC_API_KEY missing: Check .env

#### Issue: Enrichment Failing

**Symptoms:**
- Jobs reach "enriching" state but never complete
- Worker logs show Claude API errors
- Import state becomes "failed"

**Debug Steps:**
```bash
# Check worker logs for API errors
docker logs guppy-funds-worker | grep -i error

# Common error messages:
# - "API key not found" → Check ANTHROPIC_API_KEY in .env
# - "Rate limit exceeded" → Wait 1 minute and retry
# - "Invalid request" → Check Claude prompt format
```

**Solutions:**
- Verify API key: `echo $ANTHROPIC_API_KEY` in container
- Check Anthropic account has credits
- Reduce batch size in `claude_enricher.py` (Line ~80)

#### Issue: Duplicate Transactions Appearing

**Symptoms:**
- Same transaction appears multiple times
- Happens after re-uploading same CSV

**Causes:**
- Deduplication key generation changed
- CSV format changed (different column order)
- Re-processing without clearing old data

**Solutions:**
```python
# Check deduplication logic in parser
# Verify dedup_key is consistent across uploads

# To clear duplicates:
# Option 1: Delete transactions for specific import
db.transactions_enriched.delete_many({"import_id": "import_2025_..."})

# Option 2: Find actual duplicates by dedup_key
pipeline = [
    {"$group": {"_id": "$dedup_key", "count": {"$sum": 1}}},
    {"$match": {"count": {"$gt": 1}}}
]
duplicates = db.transactions_raw.aggregate(pipeline)
```

#### Issue: Frontend Shows Stale Data

**Symptoms:**
- Upload completes but transactions don't appear
- Charts show old data
- Refresh doesn't help

**Debug Steps:**
```bash
# 1. Check if data is in MongoDB
db.transactions_enriched.find().sort({date: -1}).limit(5)

# 2. Check API response
curl "http://localhost:8000/v1/transactions?limit=5"

# 3. Check browser network tab
# - Open DevTools → Network
# - Look for /v1/transactions request
# - Verify response contains new data
```

**Solutions:**
- Clear React Query cache: Hard refresh (Cmd+Shift+R)
- Check API_BASE_URL in frontend .env
- Restart frontend: `docker-compose restart frontend`
- Check React Query DevTools (browser) for cache state

#### Issue: CSV Upload Fails with 422 Error

**Symptoms:**
- API returns 422 Unprocessable Entity
- Error message: "Invalid file format" or "Validation Error"

**Causes:**
- File too large (>25MB default limit)
- Wrong file extension (not .csv)
- Invalid source_bank value

**Solutions:**
```bash
# Check file size
ls -lh your_file.csv

# Verify CSV format
head -5 your_file.csv

# Test with curl to see exact error
curl -X POST http://localhost:8000/v1/imports \
  -F "file=@your_file.csv" \
  -F "source_bank=amex" \
  -v  # verbose mode shows full error
```

**Fix:**
- Increase size limit in `app/config.py`: `MAX_FILE_SIZE_MB = 50`
- Ensure source_bank is exactly: "amex", "citi", or "wells"
- Check CSV has correct format for the bank selected

#### Issue: MongoDB Connection Failed

**Symptoms:**
- API logs: "Could not connect to MongoDB"
- Worker crashes immediately
- FastAPI won't start

**Debug Steps:**
```bash
# Test MongoDB connection
mongosh "$MONGODB_URL"

# If using Docker MongoDB:
docker ps | grep mongo

# Check MongoDB logs
docker logs guppy-funds-mongodb
```

**Solutions:**

For local MongoDB:
```bash
# Restart MongoDB container
docker-compose restart mongodb

# Check .env connection string
MONGODB_URL=mongodb://admin:admin123@mongodb:27017
```

For MongoDB Atlas:
```bash
# Verify connection string format:
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/

# Check:
# - Username/password correct
# - IP whitelist includes your IP (or 0.0.0.0/0 for development)
# - Network access configured in Atlas
```

---

## Additional Resources

### Documentation Files

**Start Here:**
- `README.md` - Project overview and quick start
- This file (`ONBOARDING.md`) - Comprehensive onboarding guide

**Architecture Specs:**
- `docs/step_5_import_job_lifecycle.md` - State machine explained
- `docs/step_6_worker_job_spec.md` - Background worker behavior
- `docs/step_7_data_processing_pipeline_spec.md` - End-to-end data flow
- `docs/step_8_spec_api.md` - API design patterns

**Data Models:**
- `docs/step_1_raw_transactions.md` - Raw transaction schema
- `docs/step_2_enriched_transactions.md` - Enriched transaction schema
- `docs/step_3_import.md` - Import job schema
- `docs/step_4_merchant.md` - Merchant cache schema

**Usage Guides:**
- `docs/API_USAGE_GUIDE.md` - Practical API examples
- `docs/SWAGGER_GUIDE.md` - Using Swagger docs
- `docs/TRANSACTION_ENDPOINTS_PLAN.md` - Transaction query patterns

### Interactive Tools

**Swagger UI:**
- URL: http://localhost:8000/docs
- Try out API endpoints
- See request/response examples
- View OpenAPI schema

**ReDoc:**
- URL: http://localhost:8000/redoc
- Alternative API documentation
- Better for reading, less for testing

**MongoDB Compass:**
- Visual database browser
- Query builder
- Index management
- Export tools

**React Query DevTools:**
- Available in dev mode at http://localhost:3000
- Bottom right corner floating icon
- See all queries, cache state, refetch behavior

### Key Files Reference

**Backend Entry Points:**
- `app/main.py` - FastAPI application setup
- `app/worker.py` - Background job processor
- `app/database.py` - MongoDB connection
- `app/config.py` - Environment configuration

**Backend Core Logic:**
- `app/api/v1/imports.py` - CSV upload handling
- `app/api/v1/transactions.py` - Transaction queries
- `app/api/v1/balances.py` - Balance calculations
- `app/api/v1/merchants.py` - Merchant directory

**Parsers:**
- `app/parsers/amex_parser.py` - AMEX CSV format
- `app/parsers/citi_parser.py` - Citi CSV format
- `app/parsers/wells_parser.py` - Wells Fargo CSV format

**AI Enrichment:**
- `app/enrichers/claude_enricher.py` - Claude API integration

**Data Models:**
- `app/models/transaction.py` - Transaction schemas
- `app/models/import_job.py` - Import job schemas
- `app/models/merchant.py` - Merchant schemas

**Frontend Entry Points:**
- `frontend/app/layout.tsx` - Root layout
- `frontend/app/page.tsx` - Dashboard
- `frontend/lib/api.ts` - API client
- `frontend/lib/types.ts` - TypeScript definitions

**Frontend Pages:**
- `frontend/app/transactions/page.tsx` - Transaction list
- `frontend/app/balances/page.tsx` - Account balances
- `frontend/app/merchants/page.tsx` - Merchant directory
- `frontend/app/import/page.tsx` - CSV upload wizard

**Frontend Hooks:**
- `frontend/hooks/useTransactions.ts` - Fetch transactions
- `frontend/hooks/useImportStatus.ts` - Poll import status
- `frontend/hooks/useBalances.ts` - Fetch balances

### External Documentation

**FastAPI:**
- Docs: https://fastapi.tiangolo.com/
- Tutorial: https://fastapi.tiangolo.com/tutorial/

**MongoDB:**
- Docs: https://www.mongodb.com/docs/
- Motor (async driver): https://motor.readthedocs.io/

**Next.js:**
- Docs: https://nextjs.org/docs
- App Router: https://nextjs.org/docs/app

**React Query:**
- Docs: https://tanstack.com/query/latest/docs/framework/react/overview
- Devtools: https://tanstack.com/query/latest/docs/framework/react/devtools

**Anthropic Claude API:**
- Docs: https://docs.anthropic.com/
- API Reference: https://docs.anthropic.com/en/api/

**TypeScript:**
- Docs: https://www.typescriptlang.org/docs/

### Getting Help

**Check Logs:**
```bash
# API logs
docker logs guppy-funds-api -f

# Worker logs (most helpful!)
docker logs guppy-funds-worker -f

# Frontend logs
docker logs guppy-funds-frontend -f

# All services
docker-compose logs -f
```

**Database Inspection:**
```bash
# Connect to MongoDB
mongosh "$MONGODB_URL"

# Switch to database
use guppy_funds

# Check collections
show collections

# Query recent imports
db.imports.find().sort({upload_time: -1}).limit(5).pretty()

# Query recent transactions
db.transactions_enriched.find().sort({date: -1}).limit(5).pretty()

# Check merchant cache
db.merchants.countDocuments()
```

**Reset Everything:**
```bash
# Stop all services
docker-compose down

# Remove volumes (clears database!)
docker-compose down -v

# Start fresh
docker-compose up -d
```

---

## Next Steps

Now that you understand the system, here are suggested next steps:

### Week 1: Familiarization
- [ ] Run through Quick Start independently
- [ ] Upload 3-5 CSV files and watch the full flow
- [ ] Explore MongoDB collections in Compass
- [ ] Try every API endpoint in Swagger
- [ ] Browse all pages in the frontend

### Week 2: Code Reading
- [ ] Read through `app/main.py` and understand FastAPI setup
- [ ] Trace a CSV upload through `imports.py` → `worker.py` → `parser` → `enricher`
- [ ] Read React Query hooks and understand caching strategy
- [ ] Review type definitions in `frontend/lib/types.ts`

### Week 3: Make Changes
- [ ] Add a new filter to transactions (follow example above)
- [ ] Add a new field to enrichment prompt
- [ ] Create a new dashboard chart
- [ ] Fix a small bug or add a small feature

### Week 4: Deep Dive
- [ ] Add a new bank parser
- [ ] Add a new aggregation endpoint
- [ ] Modify worker polling strategy
- [ ] Improve error handling somewhere

### Long Term
- [ ] Add automated tests (pytest for backend, Jest for frontend)
- [ ] Add authentication/authorization
- [ ] Implement budget tracking features
- [ ] Add data export functionality
- [ ] Deploy to production (AWS/GCP/Azure)

---

## Conclusion

You now have everything you need to understand and work with the Guppy Funds codebase. The system is well-architected, reasonably documented, and follows modern best practices.

Key things to remember:
1. **Read the code** - It's the ultimate source of truth
2. **Use the tools** - Swagger, MongoDB Compass, React Query DevTools
3. **Check the logs** - Most issues reveal themselves in logs
4. **Start small** - Make small changes first to build confidence
5. **Ask questions** - Reference the existing docs when stuck

Welcome to the project, and happy coding!

---

**Document Version:** 1.0
**Last Updated:** 2025-12-27
**Maintained By:** Carlos Chavez
