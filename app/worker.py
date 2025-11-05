"""
Background worker for processing import jobs.

Continuously monitors the imports collection and automatically processes jobs through:
uploaded → parsing → parsed → enriching → enriched → completed
"""

import asyncio
import traceback
from datetime import datetime, timedelta
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.models import ImportState
from app.parsers.amex_parser import AmexParser
from app.parsers.citi_parser import CitiParser
from app.parsers.wells_parser import WellsParser
from app.enrichers.claude_enricher import ClaudeEnricher


class ImportWorker:
    """Background worker for processing import jobs."""

    def __init__(self):
        self.client = AsyncIOMotorClient(settings.mongodb_url)
        self.db = self.client[settings.mongodb_db_name]
        self.poll_interval = 5  # seconds between polls
        self.is_running = False

    async def start(self):
        """Start the worker loop."""
        self.is_running = True
        print("🚀 Import worker started. Monitoring for jobs...")

        while self.is_running:
            try:
                await self._process_pending_jobs()
            except Exception as e:
                print(f"❌ Worker error: {e}")
                traceback.print_exc()

            # Wait before next poll
            await asyncio.sleep(self.poll_interval)

    async def stop(self):
        """Stop the worker loop."""
        self.is_running = False
        self.client.close()
        print("🛑 Import worker stopped.")

    async def _process_pending_jobs(self):
        """Find and process pending jobs."""
        # Look for jobs that need parsing (uploaded)
        uploaded_job = await self._claim_job(ImportState.UPLOADED.value)
        if uploaded_job:
            await self._process_parse(uploaded_job)
            return  # Process one job at a time

        # Look for jobs that need enrichment (parsed)
        parsed_job = await self._claim_job(ImportState.PARSED.value)
        if parsed_job:
            await self._process_enrich(parsed_job)
            return

    async def _claim_job(self, state: str) -> Optional[dict]:
        """
        Claim a job in the given state for processing.

        Uses findOneAndUpdate with a filter to atomically claim jobs,
        preventing duplicate processing by multiple workers.

        Args:
            state: The state to look for (e.g., "uploaded", "parsed")

        Returns:
            The claimed job document, or None if no jobs available
        """
        result = await self.db.imports.find_one_and_update(
            {
                "state": state,
                # Only claim jobs not recently started (prevents race conditions)
                "$or": [
                    {"started_at": {"$exists": False}},
                    {"started_at": None},
                    # Also reclaim jobs that started >5 min ago (crashed workers)
                    {"started_at": {"$lt": datetime.utcnow() - timedelta(minutes=5)}},
                ],
            },
            {
                "$set": {
                    "started_at": datetime.utcnow(),
                }
            },
            sort=[("upload_time", 1)],  # Process oldest first
        )
        return result

    async def _process_parse(self, job: dict):
        """
        Parse a CSV file and populate transactions_raw.

        Args:
            job: Import job document
        """
        import_id = job["import_id"]
        source_bank = job["source_bank"]

        print(f"📄 Parsing {import_id} ({source_bank})...")

        try:
            # Update state to parsing
            await self.db.imports.update_one(
                {"import_id": import_id},
                {"$set": {"state": ImportState.PARSING.value}},
            )

            # Select parser based on source
            if source_bank == "amex":
                parser = AmexParser(
                    file_path=job["file_path"],
                    import_id=import_id,
                    file_name=job["file_name"],
                    db=self.db,
                )
            elif source_bank == "citi":
                parser = CitiParser(
                    file_path=job["file_path"],
                    import_id=import_id,
                    file_name=job["file_name"],
                    db=self.db,
                )
            elif source_bank == "wells":
                parser = WellsParser(
                    file_path=job["file_path"],
                    import_id=import_id,
                    file_name=job["file_name"],
                    db=self.db,
                )
            else:
                raise ValueError(f"Parser for {source_bank} not yet implemented")

            # Run parser
            start_time = datetime.utcnow()
            result = await parser.parse()
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Update import with results
            await self.db.imports.update_one(
                {"import_id": import_id},
                {
                    "$set": {
                        "state": ImportState.PARSED.value,
                        "total_rows": result["total_rows"],
                        "parsed_rows": result["successful_rows"],
                        "failed_rows": result["failed_rows"],
                        "errors": result["errors"],
                        "completed_at": end_time,
                        "duration_ms": duration_ms,
                    }
                },
            )

            skipped = result.get('skipped_duplicates', 0)
            if skipped > 0:
                print(f"✅ Parsed {result['successful_rows']}/{result['total_rows']} rows in {duration_ms}ms (⏭️  {skipped} duplicates skipped)")
            else:
                print(f"✅ Parsed {result['successful_rows']}/{result['total_rows']} rows in {duration_ms}ms")

        except Exception as e:
            print(f"❌ Parse failed for {import_id}: {e}")
            traceback.print_exc()

            # Mark as failed
            await self.db.imports.update_one(
                {"import_id": import_id},
                {
                    "$set": {
                        "state": ImportState.FAILED.value,
                        "notes": f"Parsing failed: {str(e)}",
                        "completed_at": datetime.utcnow(),
                    }
                },
            )

    async def _process_enrich(self, job: dict):
        """
        Enrich parsed transactions using Claude API.

        Args:
            job: Import job document
        """
        import_id = job["import_id"]

        print(f"✨ Enriching {import_id}...")

        try:
            # Update state to enriching
            await self.db.imports.update_one(
                {"import_id": import_id},
                {"$set": {"state": ImportState.ENRICHING.value}},
            )

            # Create enricher and run enrichment
            enricher = ClaudeEnricher(import_id=import_id, db=self.db)
            start_time = datetime.utcnow()
            result = await enricher.enrich_import()
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Update import with results
            await self.db.imports.update_one(
                {"import_id": import_id},
                {
                    "$set": {
                        "state": ImportState.ENRICHED.value,
                        "enriched_rows": result["successful_rows"],
                        "completed_at": end_time,
                        "duration_ms": duration_ms,
                        "enrichment_version": 1.0,
                    }
                },
            )

            # Mark as completed
            await self.db.imports.update_one(
                {"import_id": import_id},
                {"$set": {"state": ImportState.COMPLETED.value}},
            )

            print(f"✅ Enriched {result['successful_rows']} rows in {duration_ms}ms")

        except Exception as e:
            print(f"❌ Enrich failed for {import_id}: {e}")
            traceback.print_exc()

            # Mark as failed
            await self.db.imports.update_one(
                {"import_id": import_id},
                {
                    "$set": {
                        "state": ImportState.FAILED.value,
                        "notes": f"Enrichment failed: {str(e)}",
                        "completed_at": datetime.utcnow(),
                    }
                },
            )


async def main():
    """Main entry point for the worker."""
    worker = ImportWorker()

    try:
        await worker.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down worker...")
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
