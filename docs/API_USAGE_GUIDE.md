# API Usage Guide

Complete guide to using the Guppy Funds API with practical examples.

## Table of Contents

1. [Basic Workflow](#basic-workflow)
2. [Upload Examples](#upload-examples)
3. [Monitoring Progress](#monitoring-progress)
4. [Handling Duplicates](#handling-duplicates)
5. [Common Patterns](#common-patterns)

---

## Basic Workflow

The typical flow is simple: **just upload and wait**. The worker handles everything automatically.

```bash
# 1. Upload CSV
curl -X POST http://localhost:8000/v1/imports \
  -F "file=@amex_statement.csv" \
  -F "source_bank=amex"

# Response:
{
  "import_id": "import_2025_10_28_131943",
  "state": "uploaded",
  "message": "File accepted. Import queued for processing."
}

# 2. Wait 30-60 seconds (worker processes automatically)

# 3. Done! View in MongoDB Compass
```

---

## Upload Examples

### AMEX Upload

```bash
curl -X POST http://localhost:8000/v1/imports \
  -F "file=@AMEX_statement.csv" \
  -F "source_bank=amex"
```

**Expected CSV format:**
- Headers: Date, Description, Card Member, Account #, Amount, Extended Details, Category, Reference, etc.
- Deduplication: Uses Reference field

### Citi Upload

```bash
curl -X POST http://localhost:8000/v1/imports \
  -F "file=@citi_costco.csv" \
  -F "source_bank=citi"
```

**Expected CSV format:**
- Headers: Status, Date, Description, Debit, Credit, Member Name
- Deduplication: Fingerprint hash (date + amount + description + member)

### Wells Fargo Upload

```bash
curl -X POST http://localhost:8000/v1/imports \
  -F "file=@wells_checking.csv" \
  -F "source_bank=wells"
```

**Expected CSV format:**
- No headers (columns: Date, Amount, Flag1, Flag2, Description)
- Deduplication: Fingerprint hash (date + amount + description)

---

## Monitoring Progress

### Check Import Status (via MongoDB)

The worker updates the `imports` collection automatically. You can query it:

```javascript
// In MongoDB Compass or mongosh:
db.imports.find().sort({upload_time: -1})
```

**States to watch:**
- `uploaded` - Just received, waiting for worker
- `parsing` - CSV being read
- `parsed` - Raw data stored, waiting for enrichment
- `enriching` - AI processing transactions
- `enriched` - Enrichment done
- `completed` - Fully processed
- `failed` - Error occurred (check `notes` field)

### Check Worker Logs

```bash
docker logs guppy-funds-worker --tail=50 -f
```

You'll see real-time processing:
```
🚀 Import worker started. Monitoring for jobs...
📄 Parsing import_2025_10_28_131943 (amex)...
✅ Parsed 20/20 rows in 2178ms
✨ Enriching import_2025_10_28_131943...
✅ Enriched 20 rows in 41785ms
```

---

## Handling Duplicates

### How It Works

**AMEX (Reference-based):**
```javascript
// Each transaction gets:
{
  dedup_key: "320252990053901827",  // From Reference field
  dedup_method: "reference"
}
```

**Citi/Wells (Fingerprint-based):**
```javascript
// MD5 hash of key fields:
{
  dedup_key: "a1b2c3d4e5f6...",
  dedup_method: "fingerprint"
}
```

### Testing Duplicates

Upload the same file multiple times:

```bash
# First upload
curl -X POST http://localhost:8000/v1/imports \
  -F "file=@statement.csv" \
  -F "source_bank=amex"

# Wait for completion (~40 seconds)

# Upload same file again
curl -X POST http://localhost:8000/v1/imports \
  -F "file=@statement.csv" \
  -F "source_bank=amex"

# Check logs:
docker logs guppy-funds-worker --tail=5
# You'll see: "✅ Parsed 0/20 rows (⏭️ 20 duplicates skipped)"
```

### Overlapping CSVs

If you download monthly statements with overlapping dates:

```bash
# Upload October statement (30 days)
curl -X POST http://localhost:8000/v1/imports \
  -F "file=@october.csv" \
  -F "source_bank=amex"

# Upload November statement (30 days, maybe 5 overlap with October)
curl -X POST http://localhost:8000/v1/imports \
  -F "file=@november.csv" \
  -F "source_bank=amex"

# Result: Only new transactions inserted, duplicates skipped
```

---

## Common Patterns

### Pattern 1: Manual Processing (No Worker)

If you want manual control instead of automation:

```bash
# 1. Upload
IMPORT_ID=$(curl -s -X POST http://localhost:8000/v1/imports \
  -F "file=@statement.csv" \
  -F "source_bank=amex" | jq -r '.import_id')

# 2. Parse manually
curl -X POST http://localhost:8000/v1/imports/$IMPORT_ID/parse

# 3. Enrich manually
curl -X POST http://localhost:8000/v1/imports/$IMPORT_ID/enrich
```

### Pattern 2: Batch Upload Multiple Files

```bash
# Upload all statements at once
for file in statements/*.csv; do
  curl -X POST http://localhost:8000/v1/imports \
    -F "file=@$file" \
    -F "source_bank=amex"
  echo "Uploaded: $file"
done

# Worker processes them one by one
```

### Pattern 3: Check Completion

```bash
# Poll until completed (simple bash script)
IMPORT_ID="import_2025_10_28_131943"

while true; do
  # Query MongoDB for state (requires mongosh or Compass)
  echo "Checking status..."
  sleep 10
done

# Better: Just check MongoDB Compass UI
```

### Pattern 4: Monthly Statement Workflow

```bash
# Download monthly statements from all banks
# Upload them all:

curl -X POST http://localhost:8000/v1/imports \
  -F "file=@amex_november.csv" \
  -F "source_bank=amex"

curl -X POST http://localhost:8000/v1/imports \
  -F "file=@citi_november.csv" \
  -F "source_bank=citi"

curl -X POST http://localhost:8000/v1/imports \
  -F "file=@wells_november.csv" \
  -F "source_bank=wells"

# Wait 2-3 minutes
# All transactions enriched and ready in MongoDB!
```

---

## Querying Enriched Data

Use MongoDB Compass or queries like:

### Find All Transactions for a Merchant

```javascript
db.transactions_enriched.find({
  "merchant.name": "Amazon Marketplace"
})
```

### Find Subscriptions

```javascript
db.transactions_enriched.find({
  "is_recurring": true
})
```

### Spending by Category

```javascript
db.transactions_enriched.aggregate([
  {
    $group: {
      _id: "$merchant.category",
      total: { $sum: "$amount" },
      count: { $sum: 1 }
    }
  },
  { $sort: { total: -1 } }
])
```

### Find Transactions by Date Range

```javascript
db.transactions_enriched.find({
  date: {
    $gte: ISODate("2025-10-01"),
    $lte: ISODate("2025-10-31")
  }
}).sort({ date: -1 })
```

### Check Merchant Cache

```javascript
// See all cached merchants
db.merchants.find()

// Find subscription services
db.merchants.find({ is_subscription: true })
```

---

## Performance Tips

### 1. Merchant Caching is Key

**First upload of 100 transactions:**
- ~50 unique merchants
- 50 Claude API calls
- ~$0.04 cost
- ~60-90 seconds

**Second upload (same merchants):**
- 0 API calls (all cached!)
- ~$0.001 cost
- ~10 seconds

### 2. Upload in Batches

Instead of uploading files one-by-one, upload all at once:

```bash
# Upload all three banks simultaneously
curl -X POST http://localhost:8000/v1/imports -F "file=@amex.csv" -F "source_bank=amex" &
curl -X POST http://localhost:8000/v1/imports -F "file=@citi.csv" -F "source_bank=citi" &
curl -X POST http://localhost:8000/v1/imports -F "file=@wells.csv" -F "source_bank=wells" &
wait
```

Worker processes them sequentially but you saved upload time.

### 3. Monitor Worker Logs

Keep an eye on processing:
```bash
docker logs guppy-funds-worker -f
```

---

## Error Handling

### Failed Import

If an import fails, check the import document in MongoDB:

```javascript
db.imports.findOne({ state: "failed" })
// Check the 'notes' field for error details
```

### Retry Failed Import

Currently manual - just re-upload the file. The system will:
1. Create new import
2. Skip duplicates automatically
3. Only process new transactions

### Corrupted CSV

If parsing fails:
- Check CSV encoding (should be UTF-8)
- Verify CSV structure matches expected format
- Look at worker logs for specific error

---

## Tips & Best Practices

### 1. Regular Uploads

Upload monthly statements as soon as you download them:
- Keeps data current
- Merchant cache stays warm
- Minimal API costs

### 2. Check Merchant Quality

Periodically review `merchants` collection:
- Ensure categories are correct
- Check for duplicate merchants (e.g., "Amazon" vs "Amazon Marketplace")
- You can manually merge or update merchants if needed

### 3. Database Maintenance

MongoDB Atlas handles backups, but for peace of mind:
- Export enriched transactions periodically
- Keep original CSV files as backup

### 4. Cost Management

Monitor Claude API usage:
- First month: Higher (building merchant cache)
- Ongoing: Very low (mostly cache hits)
- ~$1-2/month for typical personal use

### 5. Subscription Tracking

Use queries to track recurring expenses:

```javascript
// Find all subscriptions
db.transactions_enriched.find({ is_recurring: true })

// Monthly subscription cost
db.transactions_enriched.aggregate([
  { $match: { is_recurring: true } },
  {
    $group: {
      _id: "$merchant.name",
      monthly_cost: { $avg: "$amount" }
    }
  }
])
```

---

## Example: Complete Monthly Workflow

```bash
# 1. Download statements from all banks

# 2. Upload them
curl -X POST http://localhost:8000/v1/imports \
  -F "file=@amex_nov_2025.csv" -F "source_bank=amex"

curl -X POST http://localhost:8000/v1/imports \
  -F "file=@citi_nov_2025.csv" -F "source_bank=citi"

curl -X POST http://localhost:8000/v1/imports \
  -F "file=@wells_nov_2025.csv" -F "source_bank=wells"

# 3. Wait 2-3 minutes (watch logs if curious)
docker logs guppy-funds-worker -f

# 4. Open MongoDB Compass and explore:
# - Total spending by category
# - Subscription expenses
# - Merchant breakdown
# - Transactions by card member

# 5. Done!
```

---

## Advanced Queries

### Find Duplicate Merchants

```javascript
// Find merchants with similar names (manual cleanup)
db.merchants.find({ name: /amazon/i })
```

### Transaction Count by Bank

```javascript
db.transactions_enriched.aggregate([
  {
    $group: {
      _id: "$source_bank",
      count: { $sum: 1 },
      total: { $sum: "$amount" }
    }
  }
])
```

### Top 10 Merchants by Spend

```javascript
db.transactions_enriched.aggregate([
  {
    $group: {
      _id: "$merchant.name",
      total_spent: { $sum: "$amount" },
      transaction_count: { $sum: 1 }
    }
  },
  { $sort: { total_spent: -1 } },
  { $limit: 10 }
])
```

### Transactions by Card Member

```javascript
db.transactions_enriched.find({
  "account.card_member": "CARLOS Y CHAVEZ"
}).sort({ date: -1 })
```

---

## Troubleshooting Guide

### Issue: Enrichment Taking Too Long

**Cause:** Many new merchants requiring Claude API calls

**Solution:**
- Wait it out (first upload is always slower)
- Check worker logs for progress
- Future uploads will be faster

### Issue: Duplicate Transactions Still Appearing

**Cause:** CSV might have different Reference IDs or formatting

**Check:**
```javascript
// Find potential duplicates manually
db.transactions_raw.aggregate([
  {
    $group: {
      _id: { date: "$raw_data.Date", amount: "$raw_data.Amount", desc: "$raw_data.Description" },
      count: { $sum: 1 }
    }
  },
  { $match: { count: { $gt: 1 } } }
])
```

### Issue: Wrong Merchant Category

**Solution:** Update the merchant document:

```javascript
db.merchants.updateOne(
  { merchant_id: "amazon-marketplace" },
  {
    $set: {
      category: "Shopping",
      subcategory: "Online Retail"
    }
  }
)

// Future transactions from this merchant use updated category
```

### Issue: Worker Not Starting

**Check:**
```bash
docker ps | grep worker
docker logs guppy-funds-worker
```

**Restart:**
```bash
docker-compose restart worker
```

---

## Integration Ideas

### Export to CSV

Use MongoDB Compass or mongosh:

```bash
mongoexport --uri="your_connection_string" \
  --db=guppy_funds \
  --collection=transactions_enriched \
  --type=csv \
  --fields=date,merchant.name,amount,merchant.category \
  --out=spending_report.csv
```

### Monthly Reports

Query for specific month:

```javascript
db.transactions_enriched.find({
  date: {
    $gte: ISODate("2025-11-01"),
    $lt: ISODate("2025-12-01")
  }
})
```

### Budget Tracking

Set up views or queries:

```javascript
// Monthly spending by category
db.transactions_enriched.aggregate([
  {
    $match: {
      date: {
        $gte: ISODate("2025-11-01"),
        $lt: ISODate("2025-12-01")
      }
    }
  },
  {
    $group: {
      _id: "$merchant.category",
      total: { $sum: "$amount" }
    }
  },
  { $sort: { total: -1 } }
])
```

---

## API Response Examples

### Successful Upload

**Request:**
```bash
POST /v1/imports
```

**Response:**
```json
{
  "import_id": "import_2025_10_28_131943",
  "state": "uploaded",
  "message": "File accepted. Import queued for processing."
}
```

### Parsing Complete

**When worker finishes parsing:**

MongoDB `imports` document shows:
```json
{
  "import_id": "import_2025_10_28_131943",
  "state": "parsed",
  "total_rows": 20,
  "parsed_rows": 20,
  "failed_rows": 0,
  "duration_ms": 2178
}
```

### Enrichment Complete

**Final state:**
```json
{
  "import_id": "import_2025_10_28_131943",
  "state": "completed",
  "total_rows": 20,
  "parsed_rows": 20,
  "enriched_rows": 20,
  "failed_rows": 0,
  "duration_ms": 41785
}
```

---

## Development Workflow

### Testing New CSV Formats

```bash
# Upload test file
curl -X POST http://localhost:8000/v1/imports \
  -F "file=@test_new_format.csv" \
  -F "source_bank=amex"

# Watch logs for parsing errors
docker logs guppy-funds-worker -f

# Check raw data structure
# (Use MongoDB Compass to view transactions_raw)
```

### Clearing Test Data

**Option 1: Drop collections in Compass**
- Select collection → "Drop Collection"

**Option 2: Python script**
```python
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def clear_db():
    client = AsyncIOMotorClient("your_connection_string")
    db = client.guppy_funds

    await db.transactions_raw.delete_many({})
    await db.transactions_enriched.delete_many({})
    await db.merchants.delete_many({})
    await db.imports.delete_many({})

    print("Database cleared")
    client.close()

asyncio.run(clear_db())
```

### Reprocessing Transactions

If you update enrichment logic and want to re-enrich:

```javascript
// Mark all as unprocessed
db.transactions_raw.updateMany(
  {},
  { $set: { processed: false } }
)

// Delete enriched transactions
db.transactions_enriched.deleteMany({})

// Manually trigger enrichment
curl -X POST http://localhost:8000/v1/imports/{import_id}/enrich
```

---

## Performance Benchmarks

Based on testing:

| Metric | First Upload | Cached Upload |
|--------|--------------|---------------|
| **Parsing** | 2-8 seconds | 2-8 seconds |
| **Enrichment (20 txns)** | 40-45 seconds | 1-5 seconds |
| **Enrichment (100 txns)** | 90-120 seconds | 5-15 seconds |
| **Duplicate Detection** | ~50ms per txn | ~50ms per txn |
| **Claude API Calls** | ~1 per new merchant | ~0 (cached) |
| **Cost (100 txns)** | $0.03-0.05 | $0.001 |

---

## Summary

**The Guppy Funds API is designed to be simple:**

1. **Upload CSV** → Get import_id
2. **Wait** → Worker does everything
3. **View in Compass** → Explore enriched data

**Key Features:**
- ✅ Automatic processing
- ✅ Duplicate prevention
- ✅ AI enrichment with caching
- ✅ Multi-bank support
- ✅ Cloud-ready (MongoDB Atlas)

**For more details, see:**
- `/docs/step_*.md` - Technical specifications
- `README.md` - Project overview
- MongoDB Compass - Visual data exploration
