# Data Processing Pipeline Specification

## 🎯 Purpose

The **data processing pipeline** defines how uploaded financial data (from CSV files) is transformed into a unified, enriched transaction format.

This pipeline ensures that data from multiple heterogeneous sources (AMEX, Citi, Wells Fargo, etc.) is:
1. **Parsed** into structured raw transactions,
2. **Normalized** into a consistent schema,
3. **Enriched** with contextual information (e.g., merchant, category, derived metadata).

The pipeline operates under the supervision of the **worker loop**, which coordinates each stage and tracks its progress through the import lifecycle.

---

## 🧩 Core Components

The pipeline is composed of three main conceptual processors:

### 1️⃣ Parser
**Purpose:**  
Convert CSV files of different formats into structured transaction documents stored in `transactions_raw`.

**Responsibilities:**
- Read source CSV file (AMEX, Citi, Wells, etc.).
- Interpret column headers and map them to known internal fields.
- Validate data integrity (dates, amounts, duplicates, etc.).
- Produce uniform structured documents (even if incomplete).
- Insert parsed transactions into `transactions_raw`.

**Inputs:**
- File path of uploaded CSV.
- Source identifier (`source_bank`).

**Outputs:**
- Array of transaction documents adhering to a raw schema.
- Summary metadata (row count, parse errors, timestamps).

**Behavioral Guarantees:**
- Must be deterministic (same input CSV → same output).
- Must not mutate or filter transaction data (lossless parse).
- Must flag and record malformed rows instead of discarding them.

---

### 2️⃣ Normalizer
**Purpose:**  
Transform raw transactions from each source into a shared, **global transaction structure**.

**Responsibilities:**
- Map source-specific fields to global schema fields (e.g., “Merchant Name”, “Description”, “Posted Date”).
- Standardize data types (dates, amounts, merchant names).
- Apply consistent field names and conventions.
- Ensure every transaction includes required core fields (date, amount, merchant, etc.).

**Inputs:**
- Documents from `transactions_raw`.
- Mapping rules for the source bank schema.

**Outputs:**
- Transactions conforming to a unified schema, ready for enrichment.
- Validation summary (count of mapped, unmapped, or dropped fields).

**Behavioral Guarantees:**
- Must be idempotent (running normalization twice yields same result).
- Must retain original identifiers for traceability.
- Must log unmapped or ambiguous fields for later analysis.

---

### 3️⃣ Enricher
**Purpose:**  
Enhance normalized transactions with contextual and derived information.

**Responsibilities:**
- Add merchant metadata (category, location, brand, etc.).
- Categorize spending (e.g., “Groceries”, “Dining”, “Travel”).
- Optionally apply AI/LLM-based inference to enrich sparse data.
- Compute derived attributes (e.g., `is_subscription`, `month`, `day_of_week`).
- Produce final enriched documents for `transactions_enriched`.

**Inputs:**
- Normalized transaction documents.
- Optional enrichment configuration or models.

**Outputs:**
- Fully enriched transaction documents.
- Enrichment logs or trace metadata.

**Behavioral Guarantees:**
- Must be safe to re-run (idempotent).
- Must record enrichment version for reproducibility.
- Must isolate and log any enrichment errors per row.

---

## 🔁 Processing Flow Overview

Conceptually, each import follows this sequence:

```

Raw CSV → Parser → Normalizer → Enricher → Final Enriched Transactions

```

Each stage updates the import job state and metrics within the `imports` collection.

1. **Parser** populates `transactions_raw`
2. **Normalizer** transforms those into intermediate objects
3. **Enricher** writes the final unified form into `transactions_enriched`

---

## 🧱 Inputs and Outputs Summary

| Stage | Input | Output | Target Collection |
|--------|--------|---------|------------------|
| Parser | CSV file | Structured rows | `transactions_raw` |
| Normalizer | Parsed documents | Unified schema | (Intermediate / in-memory or temp collection) |
| Enricher | Normalized data | Enriched transactions | `transactions_enriched` |

---

## ⚙️ Pipeline-Level Responsibilities

The pipeline as a whole must:
- Maintain **data lineage** — every enriched transaction should be traceable to its raw source row.
- Guarantee **consistency** — all sources yield the same field names and structures.
- Support **reprocessing** — the same file can be re-imported without data duplication.
- Provide **transparency** — clear logging and progress tracking at every phase.
- Remain **extensible** — additional sources or enrichment steps can be added later without major refactoring.

---

## 🔍 Observability & Diagnostics

Each phase must emit structured metadata to the `imports` document, including:
- `phase_start` and `phase_end` timestamps
- counts (rows processed, errors, skipped)
- summary messages or warnings
- version identifiers for mappings and enrichment logic

These records enable real-time job status tracking and reproducible historical analysis.

---

## ✅ Summary

The **data processing pipeline** is the core transformation system that converts unstructured financial data into clean, consistent, and enriched transaction records.

- **Parser** ensures lossless ingestion.  
- **Normalizer** ensures schema consistency.  
- **Enricher** ensures contextual and analytical completeness.  

Together, they guarantee that every CSV import is traceable, uniform, and insight-ready —  
forming the foundation for future analytics, visualizations, and personal finance automation.