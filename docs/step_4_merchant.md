# merchants Collection Schema

## 🏪 Purpose
The `merchants` collection serves as a **central registry of unique merchants** derived from transaction data across all sources.  

It helps normalize merchant naming (e.g., “AMAZON MARKETPLACE NA” → “Amazon”), standardize categories, and store enrichment results like locations, aliases, or confidence scores.

By keeping merchants separate, you can:
- Reuse enrichment results instead of reprocessing every time  
- Maintain consistent categorization across transactions  
- Enable merchant-based analytics (spend by merchant, top merchants, etc.)

---

## 🧱 Document Structure

```js
{
  _id: ObjectId,
  merchant_id: String,           // unique UUID or normalized slug (e.g., "amazon-marketplace")
  name: String,                  // canonical merchant name
  aliases: [String],             // variations of name found in CSVs
  category: String,              // top-level category ("Shopping", "Food", etc.)
  subcategory: String,           // optional refined label ("Online Retail", "Fast Food")
  tags: [String],                // useful tags ("amazon", "subscription", etc.)
  website: String,               // merchant website or domain
  contact_info: {
    phone: String,
    email: String,
    support_url: String
  },
  location: {
    address: String,
    city: String,
    state: String,
    postal_code: String,
    country: String
  },
  enrichment_confidence: Number, // 0–1 confidence in enrichment
  enrichment_version: Number,    // version of enrichment model used
  created_at: ISODate,
  updated_at: ISODate
}
````

---

## 🧩 Field Details

| Field                       | Type          | Description                                                               |
| --------------------------- | ------------- | ------------------------------------------------------------------------- |
| **merchant_id**             | String        | Unique identifier or slug (e.g., `"starbucks-usa"`)                       |
| **name**                    | String        | Cleaned, canonical merchant name                                          |
| **aliases**                 | Array<String> | Raw variations of the merchant name from different sources                |
| **category**                | String        | Normalized top-level category (e.g., `"Restaurants"`, `"Transportation"`) |
| **subcategory**             | String        | Optional fine-grained classification                                      |
| **tags**                    | Array<String> | AI or user-generated tags for grouping/filtering                          |
| **website**                 | String        | Merchant’s primary website URL                                            |
| **contact_info**            | Object        | Basic merchant contact details                                            |
| **location**                | Object        | Merchant’s HQ or typical transaction location                             |
| **enrichment_confidence**   | Number        | Enrichment certainty (0–1)                                                |
| **enrichment_version**      | Number        | Version of the enrichment model used                                      |
| **created_at / updated_at** | ISODate       | Standard timestamps                                                       |

---

## 🧾 Example Documents

### 🔹 Example 1 — Amazon

```json
{
  "merchant_id": "amazon-marketplace",
  "name": "Amazon Marketplace",
  "aliases": ["AMAZON MARKETPLACE NA", "AMZN.COM/BILL WA"],
  "category": "Shopping",
  "subcategory": "Online Retail",
  "tags": ["amazon", "ecommerce", "subscription"],
  "website": "https://www.amazon.com",
  "contact_info": {
    "phone": "1-888-280-4331",
    "email": null,
    "support_url": "https://www.amazon.com/contact-us"
  },
  "location": {
    "address": "410 Terry Ave N",
    "city": "Seattle",
    "state": "WA",
    "postal_code": "98109",
    "country": "United States"
  },
  "enrichment_confidence": 0.97,
  "enrichment_version": 1.0,
  "created_at": "2025-10-27T23:00:00Z",
  "updated_at": "2025-10-27T23:00:00Z"
}
```

---

### 🔹 Example 2 — Tesla Supercharger

```json
{
  "merchant_id": "tesla-supercharger",
  "name": "Tesla Supercharger",
  "aliases": ["TESLA SUPERCHARGER US", "TESLA INC CHARGING"],
  "category": "Transportation",
  "subcategory": "EV Charging",
  "tags": ["tesla", "ev", "charging"],
  "website": "https://www.tesla.com/supercharger",
  "location": {
    "city": "Campbell",
    "state": "CA",
    "country": "United States"
  },
  "enrichment_confidence": 0.94,
  "created_at": "2025-10-27T23:05:00Z",
  "updated_at": "2025-10-27T23:05:00Z"
}
```

---

## ⚙️ Indexing Recommendations

```js
db.merchants.createIndex({ merchant_id: 1 }, { unique: true });
db.merchants.createIndex({ name: 1 });
db.merchants.createIndex({ category: 1 });
db.merchants.createIndex({ aliases: 1 });
db.merchants.createIndex({ tags: 1 });
```

---

## 🧭 Usage in Enrichment Workflow

1. During enrichment, a transaction’s `merchant.name` is matched (fuzzy or exact) against this collection.
2. If found → reuse normalized fields (`category`, `location`, etc.)
3. If not found → generate new `merchant` document via enrichment logic.
4. Transactions reference this merchant via the normalized `merchant.name` or `merchant_id`.

---

## ✅ Summary

* Central cache for merchant normalization & enrichment
* Prevents redundant lookups and AI calls
* Enables fast analytics (e.g., spend by merchant or category)
* Improves consistency across all `transactions_enriched` records