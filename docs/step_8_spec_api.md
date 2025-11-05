# API Specification (v1)

## 🎯 Purpose

This API defines the **interface layer** for the local ingestion and enrichment service.  
It provides endpoints to upload CSVs, monitor job progress, retry failed imports, and trigger data enrichment.

This API is designed for **personal, local use** — it is not public-facing.  
It runs inside the same Docker network as the worker and MongoDB containers.

---

## ⚙️ General Characteristics

| Property | Value |
|-----------|--------|
| **Version** | v1 |
| **Base URL** | `http://localhost:8000/v1` |
| **Auth** | None (local-only) |
| **Content Types** | `application/json`, `multipart/form-data` |
| **Max File Size** | 25MB (recommended) |
| **File Types Supported** | `.csv` |
| **Rate Limits** | None (local-only) |
| **Error Format** | JSON (see below) |

---

## ⚠️ Error Model

All failed requests return a standard JSON error structure:

```json
{
  "error": {
    "code": "IMPORT_FAILED",
    "message": "Parsing failed due to malformed CSV",
    "details": {
      "line": 12,
      "reason": "missing column"
    }
  }
}
````

| Field       | Type   | Description                                            |
| ----------- | ------ | ------------------------------------------------------ |
| **code**    | String | Short machine-readable error code.                     |
| **message** | String | Human-readable summary of the problem.                 |
| **details** | Object | Optional structured context (e.g., row number, field). |

Common HTTP codes:

* `200 OK` — success
* `400 Bad Request` — invalid input
* `404 Not Found` — import not found
* `409 Conflict` — duplicate upload
* `500 Internal Server Error` — unexpected system failure

---

## 🧩 Endpoints Overview

| Method | Path                             | Description                                                         |
| ------ | -------------------------------- | ------------------------------------------------------------------- |
| `POST` | `/v1/imports`                    | Upload a CSV and create a new import job.                           |
| `GET`  | `/v1/imports`                    | List all recent imports and their statuses.                         |
| `GET`  | `/v1/imports/{import_id}/status` | View detailed status and progress for a specific import.            |
| `POST` | `/v1/imports/{import_id}/retry`  | Retry a failed or incomplete import job.                            |
| `POST` | `/v1/imports/{import_id}/enrich` | Enrich data for a specific import (if enrichment not yet complete). |
| `POST` | `/v1/enrich`                     | Enrich all unprocessed raw transactions across imports.             |

---

## 📥 1️⃣ `POST /v1/imports`

**Purpose:**
Accepts a CSV upload, stores the file, and creates a new import record in the `imports` collection.
Triggers the worker loop to begin processing.

**Request:**

* **Content-Type:** `multipart/form-data`
* **Body:**

  * `file`: The CSV file to import
  * `source_bank`: One of `["amex", "citi", "wells"]`

**Response (201):**

```json
{
  "import_id": "import_2025_10_28_1",
  "state": "uploaded",
  "message": "File accepted. Import queued for processing."
}
```

---

## 📊 2️⃣ `GET /v1/imports`

**Purpose:**
Lists recent imports with summary metadata for monitoring and visibility.

**Response (200):**

```json
{
  "imports": [
    {
      "import_id": "import_2025_10_27_1",
      "source_bank": "amex",
      "state": "enriching",
      "parsed_rows": 120,
      "enriched_rows": 56,
      "failed_rows": 0,
      "started_at": "2025-10-27T22:32:10Z"
    },
    {
      "import_id": "import_2025_10_25_3",
      "source_bank": "citi",
      "state": "completed",
      "parsed_rows": 84,
      "enriched_rows": 84
    }
  ]
}
```

---

## 🔍 3️⃣ `GET /v1/imports/{import_id}/status`

**Purpose:**
Returns detailed progress and current state for a single import job.

**Response (200):**

```json
{
  "import_id": "import_2025_10_27_1",
  "state": "enriching",
  "progress": {
    "phase": "enrichment",
    "total_rows": 120,
    "processed_rows": 56,
    "remaining_rows": 64
  },
  "timestamps": {
    "uploaded_at": "2025-10-27T22:30:00Z",
    "started_at": "2025-10-27T22:32:10Z"
  },
  "errors": []
}
```

---

## 🔁 4️⃣ `POST /v1/imports/{import_id}/retry`

**Purpose:**
Retries a failed import job.
The service resumes from the last successfully completed phase (`parsed` → `enriching`).

**Response (202):**

```json
{
  "import_id": "import_2025_10_27_1",
  "previous_state": "failed",
  "new_state": "parsing",
  "message": "Import job re-queued for processing."
}
```

---

## ⚙️ 5️⃣ `POST /v1/imports/{import_id}/enrich`

**Purpose:**
Triggers enrichment for a specific import whose parsing is already complete.

**Response (202):**

```json
{
  "import_id": "import_2025_10_27_1",
  "state": "enriching",
  "message": "Enrichment started for parsed transactions."
}
```

---

## 🧠 6️⃣ `POST /v1/enrich`

**Purpose:**
Global enrichment — processes all raw transactions across imports that haven’t yet been enriched.

**Response (200):**

```json
{
  "total_enriched": 453,
  "message": "Enrichment completed for all pending transactions."
}
```

---

## 💬 Additional Notes

* All endpoints are designed to **return immediately** — heavy processing occurs asynchronously in the worker loop.
* Progress is tracked entirely through the `imports` collection, viewable via the `/status` endpoints.
* The API and worker communicate only via MongoDB state changes (no message broker).
* In Docker Compose, this API runs on the same network as MongoDB and the worker, typically exposed on port **8000**.

---

## ✅ Summary

This API provides the minimal control surface for managing and observing the ingestion pipeline:

| Endpoint               | Primary Function         |
| ---------------------- | ------------------------ |
| `/imports`             | Upload and initiate jobs |
| `/imports/status`      | Monitor progress         |
| `/imports/{id}/retry`  | Recover from failure     |
| `/imports/{id}/enrich` | Enrich specific imports  |
| `/enrich`              | Global enrichment        |

Together, they create a lightweight, self-contained interface for orchestrating and monitoring the entire financial ingestion workflow.