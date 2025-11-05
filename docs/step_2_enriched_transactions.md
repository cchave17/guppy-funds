# transactions_enriched Collection Schema

## 🎯 Purpose
The `transactions_enriched` collection holds **clean, standardized, and enriched** transaction data consolidated from all sources (AMEX, Wells Fargo, Citi, etc.).  

Each document here follows a **universal schema** that unifies data formats, adds inferred fields (via enrichment/LLM), and provides a single source of truth for your finance API.

---

## 🧱 Document Structure

```js
{
  _id: ObjectId,
  transaction_id: String,       // unique UUID or generated ID for the transaction
  source_bank: String,          // "amex" | "citi" | "wells"
  import_id: String,            // links back to batch in `imports`
  raw_id: ObjectId,             // reference to original document in transactions_raw
  enrichment_version: Number,   // version of enrichment logic used
  date: ISODate,                // normalized date
  description: String,          // cleaned transaction description
  amount: Number,               // always positive, use `type` to indicate debit/credit
  type: String,                 // "debit" | "credit" | "transfer"
  currency: String,             // ISO 4217 code, e.g., "USD"
  merchant: {
    name: String,
    category: String,           // normalized (e.g., "Restaurants", "Groceries")
    subcategory: String,        // optional (e.g., "Fast Food")
    location: {
      address: String,
      city: String,
      state: String,
      postal_code: String,
      country: String
    }
  },
  account: {
    name: String,               // e.g., "Wells Fargo Checking"
    account_number: String,     // masked or last 4
    card_member: String         // e.g., "Carlos Y Chavez" or "Nahnsu Dawkins"
  },
  tags: [String],               // user or AI-generated tags (e.g., ["food", "travel"])
  notes: String,                // optional free-text notes
  is_recurring: Boolean,        // whether it’s a repeating payment
  enriched_confidence: Number,  // 0–1 confidence score from enrichment model
  created_at: ISODate,          // record creation
  updated_at: ISODate           // last enrichment or update
}
````

---

## 🧩 Field Details

| Field                       | Type          | Description                                            |
| --------------------------- | ------------- | ------------------------------------------------------ |
| **transaction_id**          | String        | Unique transaction identifier (UUID or hash)           |
| **source_bank**             | String        | Bank source label (`"amex"`, `"citi"`, `"wells"`)      |
| **import_id**               | String        | Batch import reference                                 |
| **raw_id**                  | ObjectId      | Link to original document in `transactions_raw`        |
| **enrichment_version**      | Number        | Version tag for enrichment logic                       |
| **date**                    | ISODate       | Parsed and standardized transaction date               |
| **description**             | String        | Cleaned human-readable description                     |
| **amount**                  | Number        | Transaction amount (absolute value)                    |
| **type**                    | String        | Transaction type (`"debit"`, `"credit"`, `"transfer"`) |
| **currency**                | String        | ISO code (usually `"USD"`)                             |
| **merchant**                | Object        | Merchant details and location                          |
| **account**                 | Object        | Bank account info including card member                |
| **tags**                    | Array<String> | User or LLM-generated tags                             |
| **notes**                   | String        | Optional comments                                      |
| **is_recurring**            | Boolean       | Indicates recurring charges/subscriptions              |
| **enriched_confidence**     | Number        | Confidence score (0–1) for enrichment quality          |
| **created_at / updated_at** | ISODate       | Standard timestamps                                    |

---

## 🧾 Example Documents

### 🔹 AMEX Example

```json
{
  "transaction_id": "7e2b21c0-27af-4a9e-bb40-88b81cdd9f95",
  "source_bank": "amex",
  "import_id": "import_2025_10_27_1",
  "raw_id": "671ebd5c2a0fdc002ab2fa6d",
  "enrichment_version": 1.0,
  "date": "2025-10-25T00:00:00Z",
  "description": "AMAZON MARKETPLACE NA",
  "amount": 77.04,
  "type": "debit",
  "currency": "USD",
  "merchant": {
    "name": "Amazon Marketplace",
    "category": "Shopping",
    "subcategory": "Online Retail",
    "location": {
      "address": "410 Terry Ave N",
      "city": "Seattle",
      "state": "WA",
      "postal_code": "98109",
      "country": "United States"
    }
  },
  "account": {
    "name": "AMEX Platinum",
    "account_number": "91016",
    "card_member": "Carlos Y Chavez"
  },
  "tags": ["shopping", "amazon", "ecommerce"],
  "is_recurring": false,
  "enriched_confidence": 0.98,
  "created_at": "2025-10-27T22:45:00Z",
  "updated_at": "2025-10-27T22:45:00Z"
}
```

---

### 🔹 Citi Example

```json
{
  "transaction_id": "6f94c2de-9b09-42f8-a05d-78b66dded91c",
  "source_bank": "citi",
  "import_id": "import_2025_10_27_2",
  "raw_id": "671ebd5c2a0fdc002ab2fa8f",
  "enrichment_version": 1.0,
  "date": "2025-10-24T00:00:00Z",
  "description": "TESLA SUPERCHARGER US 877-7983752 CA",
  "amount": 10.29,
  "type": "debit",
  "currency": "USD",
  "merchant": {
    "name": "Tesla Supercharger",
    "category": "Transportation",
    "subcategory": "EV Charging",
    "location": {
      "address": null,
      "city": "Campbell",
      "state": "CA",
      "postal_code": null,
      "country": "United States"
    }
  },
  "account": {
    "name": "Citi Costco Visa",
    "account_number": null,
    "card_member": "Carlos Y Chavez"
  },
  "tags": ["tesla", "charging", "transportation"],
  "is_recurring": false,
  "enriched_confidence": 0.92,
  "created_at": "2025-10-27T22:50:00Z",
  "updated_at": "2025-10-27T22:50:00Z"
}
```

---

### 🔹 Wells Fargo Example

```json
{
  "transaction_id": "a1b3d7f2-9f35-4b8b-bb2d-f6ccad3c8e31",
  "source_bank": "wells",
  "import_id": "import_2025_10_27_3",
  "raw_id": "671ebd5c2a0fdc002ab2fa99",
  "enrichment_version": 1.0,
  "date": "2025-10-27T00:00:00Z",
  "description": "ATM WITHDRAWAL AUTHORIZED ON 10/25 1156 Vierling Dr E Shakopee MN",
  "amount": 500.00,
  "type": "debit",
  "currency": "USD",
  "merchant": {
    "name": "Wells Fargo ATM",
    "category": "Cash Withdrawal",
    "subcategory": "ATM",
    "location": {
      "address": "1156 Vierling Dr E",
      "city": "Shakopee",
      "state": "MN",
      "postal_code": null,
      "country": "United States"
    }
  },
  "account": {
    "name": "Wells Fargo Checking",
    "account_number": null,
    "card_member": "Nahnsu Dawkins"
  },
  "tags": ["atm", "cash"],
  "is_recurring": false,
  "enriched_confidence": 0.95,
  "created_at": "2025-10-27T22:55:00Z",
  "updated_at": "2025-10-27T22:55:00Z"
}
```

---

## ⚙️ Indexing Recommendations

```js
db.transactions_enriched.createIndex({ transaction_id: 1 }, { unique: true });
db.transactions_enriched.createIndex({ date: -1 });
db.transactions_enriched.createIndex({ source_bank: 1 });
db.transactions_enriched.createIndex({ "merchant.name": 1 });
db.transactions_enriched.createIndex({ "merchant.category": 1 });
db.transactions_enriched.createIndex({ "account.card_member": 1 });
db.transactions_enriched.createIndex({ tags: 1 });
```

---

## ✅ Summary

* **Unified, enrichment-ready schema** for all sources
* Added `card_member` to clearly identify who made the transaction
* Fully traceable via `raw_id` + `import_id`
* Optimized for **joint account querying, analytics, and API access**
* Future-safe if you expand to multi-user handling later