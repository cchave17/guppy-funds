# Worker Loop Specification

## 🎯 Purpose

The **worker loop** is a background process responsible for monitoring and processing import jobs within the system.  
Its role is to ensure that uploaded CSV files move reliably through the full lifecycle — from upload, to parsing, to enrichment, to completion — without requiring external brokers or manual intervention.

---

## 🧠 Core Problem to Solve

The system must automatically detect new import jobs (`state: "uploaded"`) and progress them through the defined lifecycle while:
- maintaining visibility into each phase’s progress,
- ensuring data integrity (no duplicate or partial processing),
- and providing recoverability if the service restarts or fails mid-job.

The worker loop is the mechanism that provides this **continuity and automation**.

---

## 🧩 Responsibilities

The worker loop must:

1. **Monitor Import States**
   - Periodically check the `imports` collection for jobs requiring action (e.g., `uploaded`, `parsed`, or `failed` waiting for retry).
   - Determine which job(s) are ready to process.

2. **Advance Job Lifecycle**
   - Transition jobs through their lifecycle states:  
     `uploaded → parsing → parsed → enriching → enriched → completed`.
   - Update job metadata (progress, timestamps, error counts, etc.) as processing continues.

3. **Ensure Single Ownership**
   - Prevent the same import from being processed by multiple workers simultaneously.
   - Provide a mechanism to “lock” or “claim” a job while it’s being processed.

4. **Handle Failures Gracefully**
   - Detect and record errors (e.g., file read issues, parsing errors, enrichment exceptions).
   - Mark the job `failed` with diagnostic information and preserve partial progress.
   - Support later reprocessing or retry logic.

5. **Guarantee Recoverability**
   - On startup, resume any job left in an unfinished state (e.g., `parsing`, `enriching`).
   - Avoid starting new jobs until previous incomplete ones are reconciled.

6. **Provide Observability**
   - Ensure job progress and phase timestamps are always queryable through MongoDB.
   - Maintain sufficient metadata for the API to return clear status responses.

---

## 🔁 Operational Overview

Conceptually, the worker loop operates continuously alongside the API service:

1. Detects pending imports in `imports` (e.g., `state: "uploaded"`).
2. Claims one job at a time and updates its state to `"parsing"`.
3. Runs the required step (parsing or enrichment) using the corresponding data processor.
4. Updates the job state and metrics in MongoDB.
5. Moves to the next available job or waits until the next cycle.

This continuous cycle ensures that uploaded files are automatically processed into fully enriched transaction data without manual intervention.

---

## 🧱 Inputs and Outputs

**Inputs**
- `imports` documents in specific actionable states (`uploaded`, `parsed`, etc.)
- Access to stored CSV files (via file path recorded in metadata)
- Configuration for processing frequency and parallelism

**Outputs**
- Updated job states in `imports` (reflecting lifecycle progression)
- Populated collections (`transactions_raw`, `transactions_enriched`)
- Error logs and job metrics (counts, timestamps, etc.)

---

## 🔒 Behavioral Guarantees

The worker loop must guarantee:

1. **Idempotency:**  
   Processing the same import twice should not create duplicate records.

2. **Atomic Transitions:**  
   Each state transition should be explicit and recorded — a job is never between states.

3. **Persistence:**  
   All progress, even partial, must be visible in MongoDB for recovery and monitoring.

4. **Isolation:**  
   Each job runs independently; failure in one does not affect others.

5. **Continuity:**  
   Restarting the service must not lose context; the loop resumes where it left off.

---

## 🧩 Related Components

- **`imports` collection** — Source of truth for job status and metadata.
- **`transactions_raw` collection** — Stores parsed rows from CSV.
- **`transactions_enriched` collection** — Stores normalized and enriched transactions.
- **FastAPI API Layer** — Provides upload and status endpoints; does not execute processing itself.

---

## ✅ Summary

The worker loop acts as the **autonomous controller** that keeps the ingestion pipeline flowing.  
It ensures that every import progresses predictably and transparently from upload to completion —  
even in the absence of external message brokers or manual triggers.

Its role is not to define *how* parsing or enrichment is implemented,  
but to guarantee *that they happen*, *in the right order*, *reliably*, and *with full observability*.