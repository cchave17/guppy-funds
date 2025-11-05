# Import Job Lifecycle

## 🎯 Purpose
This document defines the **lifecycle states**, **transitions**, and **metadata** for import jobs in the personal finance ingestion service.

Each import represents a single uploaded CSV file (from AMEX, Citi, Wells Fargo, etc.) and tracks its entire journey through parsing, enrichment, and completion.

---

## 🧭 Lifecycle States

| State | Description | Next Possible States |
|--------|--------------|----------------------|
| **uploaded** | File has been received and registered in the `imports` collection. No parsing has started yet. | `parsing`, `failed` |
| **parsing** | The file is being parsed, and transactions are being inserted into `transactions_raw`. | `parsed`, `failed` |
| **parsed** | Parsing complete; all rows successfully inserted. Awaiting enrichment. | `enriching`, `failed` |
| **enriching** | Enrichment and normalization in progress (mapping to unified schema, merchant lookup, etc.). | `enriched`, `failed` |
| **enriched** | Enrichment process finished successfully. Data written to `transactions_enriched`. | `completed` |
| **completed** | Final state. The import was processed successfully and fully enriched. | — |
| **failed** | Job failed due to errors (e.g., parsing or enrichment issues). Manual retry required. | (Manual retry → `parsing` or `enriching`) |

---

## 🔄 Typical State Flow

```

uploaded → parsing → parsed → enriching → enriched → completed
↘
failed (recoverable or final)

````

---

## 🧱 Metadata Fields (Stored in `imports` Collection)

| Field | Type | Description |
|--------|------|-------------|
| **import_id** | String | Unique identifier for the import job (e.g., `import_2025_10_27_1`). |
| **source_bank** | String | The financial source of the file (`amex`, `citi`, `wells`). |
| **file_name** | String | Name of the uploaded CSV file. |
| **file_path** | String | Storage path or location of the uploaded file. |
| **upload_time** | ISODate | Timestamp when the file was uploaded. |
| **state** | String | Current job state (see lifecycle above). |
| **total_rows** | Number | Total number of rows parsed from the file. |
| **parsed_rows** | Number | Rows successfully parsed and inserted into `transactions_raw`. |
| **enriched_rows** | Number | Rows successfully enriched and stored in `transactions_enriched`. |
| **failed_rows** | Number | Optional count of failed rows. |
| **started_at** | ISODate | Timestamp when current phase started. |
| **completed_at** | ISODate | Timestamp when the phase completed. |
| **duration_ms** | Number | Time elapsed for the current phase. |
| **errors** | Array | Array of error objects with row number, message, and timestamp. |
| **enrichment_version** | Number | Version of the enrichment logic used for this job. |
| **notes** | String | Optional free-form comments or diagnostic info. |

---

## 🧩 Example Document

```json
{
  "import_id": "import_2025_10_27_1",
  "source_bank": "amex",
  "file_name": "AMEX.csv",
  "file_path": "/uploads/AMEX.csv",
  "upload_time": "2025-10-27T22:30:00Z",
  "state": "enriching",
  "total_rows": 122,
  "parsed_rows": 122,
  "enriched_rows": 56,
  "failed_rows": 0,
  "started_at": "2025-10-27T22:32:10Z",
  "completed_at": null,
  "duration_ms": null,
  "errors": [],
  "enrichment_version": 1.0,
  "notes": "Enrichment running normally."
}
````

---

## 🔁 State Transition Rules

| From State                   | To State                                                       | Condition / Trigger |
| ---------------------------- | -------------------------------------------------------------- | ------------------- |
| uploaded → parsing           | File registered; background parser starts.                     |                     |
| parsing → parsed             | All rows written successfully to `transactions_raw`.           |                     |
| parsing → failed             | Parsing encountered unrecoverable error (e.g., corrupted CSV). |                     |
| parsed → enriching           | Enrichment job starts (either auto or manual trigger).         |                     |
| enriching → enriched         | Enrichment and normalization finished successfully.            |                     |
| enriching → failed           | Enrichment failed due to logic or data errors.                 |                     |
| enriched → completed         | Job finalization complete, summary updated.                    |                     |
| * → failed                   | Any stage error that halts the job.                            |                     |
| failed → parsing / enriching | Manual retry initiated.                                        |                     |

---

## 🧠 Design Rationale

* **Clarity:** Each job has a single, well-defined state.
* **Recoverability:** Jobs can safely resume or retry from intermediate states.
* **Observability:** Each state is timestamped for traceability.
* **Scalability:** This state model fits async, queued, or distributed processing.
* **Persistence:** All state changes are stored in MongoDB, enabling status endpoints.

---

## ✅ Summary

This lifecycle ensures a clear and reliable process for managing the ingestion and enrichment of financial data:

* Deterministic state transitions
* Robust error handling
* Clear metrics and traceability
* Compatible with both synchronous and background job systems