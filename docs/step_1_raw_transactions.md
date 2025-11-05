# transactions_raw Collection Schema

## 🧾 Purpose
The `transactions_raw` collection stores **unaltered rows** imported from all financial sources (AMEX, Citi, Wells Fargo, etc.).  
Each document represents a single transaction record exactly as it appeared in the source CSV, along with metadata for traceability and ingestion management.

This collection serves as the **immutable foundation** for enrichment, debugging, and re-processing.

---

## 🧱 Document Structure

```js
{
  _id: ObjectId,
  source_bank: String,          // "amex" | "citi" | "wells"
  import_id: String,            // unique batch ID for the CSV import (e.g. "import_2025_10_27_1")
  raw_data: Object,             // original CSV row as key:value pairs
  file_name: String,            // name of the uploaded CSV file
  created_at: ISODate,          // when this row was inserted
  processed: Boolean,           // whether it has been enriched
  notes: String,                // optional comments or error notes
  raw_text: String              // concatenated line of the original CSV row (for LLM enrichment/debug)
}
````

---

## 🧩 Field Details

| Field           | Type     | Description                                                                            |
| --------------- | -------- | -------------------------------------------------------------------------------------- |
| **_id**         | ObjectId | Auto-generated MongoDB ID                                                              |
| **source_bank** | String   | Identifier of the financial source (e.g., `"amex"`, `"citi"`, `"wells"`)               |
| **import_id**   | String   | Unique identifier for the CSV import batch; useful for deduplication and grouping      |
| **raw_data**    | Object   | Key-value map of the CSV row, preserving original column headers                       |
| **file_name**   | String   | Original file name for reference                                                       |
| **created_at**  | ISODate  | Timestamp when the document was stored                                                 |
| **processed**   | Boolean  | `true` once this transaction has been enriched and migrated to `transactions_enriched` |
| **notes**       | String   | Optional free-text for parser logs or error info                                       |
| **raw_text**    | String   | Concatenated raw CSV line — helps when re-enriching or debugging parsing logic         |

---

## 🧾 Example Documents

### 🔹 AMEX Example

```json
{
  "source_bank": "amex",
  "import_id": "import_2025_10_27_1",
  "file_name": "AMEX.csv",
  "created_at": "2025-10-27T22:30:00Z",
  "processed": false,
  "raw_text": "10/25/2025, AMAZON MARKETPLACE NA, 77.04, Merchandise & Supplies-Internet Purchase",
  "raw_data": {
    "Date": "10/25/2025",
    "Description": "AMAZON MARKETPLACE NA",
    "Card Member": "NAHNSU L DAWKINS",
    "Account #": "-91016",
    "Amount": 77.04,
    "Extended Details": "AMAZON MARKETPLACE NA",
    "Appears On Your Statement As": "AMAZON MARKETPLACE NAMZN.COM/BILL WA",
    "Address": "410 TERRY AVE N",
    "City/State": "SEATTLE, WA",
    "Zip Code": "98109",
    "Country": "UNITED STATES",
    "Reference": "320252990053901827",
    "Category": "Merchandise & Supplies-Internet Purchase"
  }
}
```

### 🔹 Citi Example

```json
{
  "source_bank": "citi",
  "import_id": "import_2025_10_27_2",
  "file_name": "citi_costco_statement.csv",
  "created_at": "2025-10-27T22:31:00Z",
  "processed": false,
  "raw_text": "10/24/2025, TESLA SUPERCHARGER US 877-7983752 CA, 10.29, CARLOS Y CHAVEZ CAMPOS",
  "raw_data": {
    "Status": "Cleared",
    "Date": "10/24/2025",
    "Description": "TESLA SUPERCHARGER US 877-7983752 CA",
    "Debit": 10.29,
    "Credit": null,
    "Member Name": "CARLOS Y CHAVEZ CAMPOS"
  }
}
```

### 🔹 Wells Fargo Example

```json
{
  "source_bank": "wells",
  "import_id": "import_2025_10_27_3",
  "file_name": "Wells_fargo.csv",
  "created_at": "2025-10-27T22:32:00Z",
  "processed": false,
  "raw_text": "10/27/2025, -500.00, ATM WITHDRAWAL AUTHORIZED ON 10/25 1156 Vierling Dr E Shakopee MN",
  "raw_data": {
    "Date": "10/27/2025",
    "Amount": -500.00,
    "Transaction Type": "ATM WITHDRAWAL AUTHORIZED ON 10/25 1156 Vierling Dr E Shakopee MN",
    "Notes": null
  }
}
```

---

## 🧭 Indexing Recommendations

```js
db.transactions_raw.createIndex({ import_id: 1 });
db.transactions_raw.createIndex({ source_bank: 1 });
db.transactions_raw.createIndex({ processed: 1 });
db.transactions_raw.createIndex({ created_at: -1 });
```

---

## ✅ Summary

* **One collection for all raw imports**
* **Consistent top-level metadata**
* **Flexible inner `raw_data` schema**
* Enables full traceability and safe re-enrichment
* Keeps ingestion simple and Mongo-native
