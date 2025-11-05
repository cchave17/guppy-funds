# imports Collection Schema

## 📦 Purpose
The `imports` collection tracks **each file upload** (CSV, Excel, etc.) and manages the ingestion and enrichment lifecycle of those imports.

Each document represents one uploaded file and provides:
- A unique identifier (`import_id`)
- Metadata about the source and upload event
- Counts of parsed and processed rows
- Timestamps for ingestion and enrichment
- Error logging for transparency and retries

This enables deduplication, status tracking, and re-enrichment of specific imports.

---

## 🧱 Document Structure

```js
{
  _id: ObjectId,
  import_id: String,           // e.g., "import_2025_10_27_1"
  source_bank: String,         // "amex" | "citi" | "wells"
  file_name: String,           // original uploaded filename
  file_path: String,           // optional if stored locally or on S3
  upload_time: ISODate,        // when file was received
  total_rows: Number,          // total number of rows parsed
  processed_rows: Number,      // rows successfully enriched
  status: String,              // "uploaded" | "parsed" | "enriched" | "failed"
  checksum: String,            // optional MD5/SHA1 of file for deduplication
  errors: [                    // array of error objects (if any)
    {
      row_number: Number,
      message: String,
      timestamp: ISODate
    }
  ],
  started_at: ISODate,         // enrichment job start time
  completed_at: ISODate,       // enrichment job completion time
  duration_ms: Number,         // optional processing duration
  notes: String                // free-form comments or logs
}
````

---

## 🧩 Field Details

| Field                         | Type    | Description                                                       |
| ----------------------------- | ------- | ----------------------------------------------------------------- |
| **import_id**                 | String  | Unique ID assigned at upload time; referenced in all transactions |
| **source_bank**               | String  | Source label (“amex”, “citi”, “wells”)                            |
| **file_name**                 | String  | Original file name as uploaded                                    |
| **file_path**                 | String  | Optional path to storage location (e.g., S3 URI, local dir)       |
| **upload_time**               | ISODate | When file was received                                            |
| **total_rows**                | Number  | Total rows parsed from CSV                                        |
| **processed_rows**            | Number  | Rows successfully enriched                                        |
| **status**                    | String  | Current stage of processing                                       |
| **checksum**                  | String  | Optional file hash for deduplication                              |
| **errors**                    | Array   | Collection of parsing/enrichment errors                           |
| **started_at / completed_at** | ISODate | Job lifecycle timestamps                                          |
| **duration_ms**               | Number  | Time taken for enrichment process                                 |
| **notes**                     | String  | Optional comments or diagnostic info                              |

---

## 🧾 Example Documents

### 🔹 AMEX Example

```json
{
  "import_id": "import_2025_10_27_1",
  "source_bank": "amex",
  "file_name": "AMEX.csv",
  "file_path": "/uploads/AMEX.csv",
  "upload_time": "2025-10-27T22:30:00Z",
  "total_rows": 122,
  "processed_rows": 122,
  "status": "enriched",
  "checksum": "ab12cd34ef56...",
  "started_at": "2025-10-27T22:30:10Z",
  "completed_at": "2025-10-27T22:32:05Z",
  "duration_ms": 115000,
  "notes": "Full enrichment succeeded."
}
```

---

### 🔹 Citi Example (with errors)

```json
{
  "import_id": "import_2025_10_27_2",
  "source_bank": "citi",
  "file_name": "citi_costco_statement.csv",
  "upload_time": "2025-10-27T22:35:00Z",
  "total_rows": 95,
  "processed_rows": 93,
  "status": "failed",
  "errors": [
    { "row_number": 45, "message": "Missing Date field", "timestamp": "2025-10-27T22:37:00Z" },
    { "row_number": 78, "message": "Invalid amount format", "timestamp": "2025-10-27T22:37:30Z" }
  ],
  "notes": "2 rows skipped due to parse errors."
}
```

---

## ⚙️ Indexing Recommendations

```js
db.imports.createIndex({ import_id: 1 }, { unique: true });
db.imports.createIndex({ source_bank: 1 });
db.imports.createIndex({ upload_time: -1 });
db.imports.createIndex({ status: 1 });
```

---

## ✅ Summary

* Central registry for file uploads and enrichment jobs
* Links to `transactions_raw` and `transactions_enriched` via `import_id`
* Enables deduplication, monitoring, and debugging
* Ideal for admin dashboards or re-processing logic