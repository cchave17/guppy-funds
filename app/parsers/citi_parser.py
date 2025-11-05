import csv
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.models import TransactionRaw


class CitiParser:
    """Parser for Citi CSV files."""

    def __init__(self, file_path: str, import_id: str, file_name: str, db=None):
        self.file_path = Path(file_path)
        self.import_id = import_id
        self.file_name = file_name
        self.db = db

    async def parse(self) -> dict:
        """
        Parse Citi CSV and insert into transactions_raw collection.
        Uses fingerprint-based duplicate detection.

        Returns:
            Dictionary with parsing statistics including skipped duplicates
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        total_rows = 0
        successful_rows = 0
        skipped_duplicates = 0
        errors = []

        with open(self.file_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row_num, row in enumerate(reader, start=2):
                try:
                    total_rows += 1

                    # Determine amount and type from Debit/Credit columns
                    debit = row.get('Debit', '').strip()
                    credit = row.get('Credit', '').strip()

                    if debit:
                        amount = float(debit)
                        transaction_type = "debit"
                    elif credit:
                        amount = float(credit)
                        transaction_type = "credit"
                    else:
                        amount = 0.0
                        transaction_type = "unknown"

                    # Create raw_text
                    raw_text = f"{row.get('Date', '')}, {row.get('Description', '')}, {amount}, {row.get('Member Name', '')}"

                    # Generate fingerprint for deduplication
                    # Using: date + amount + description + member_name
                    fingerprint_data = f"citi_{row.get('Date', '')}_{amount}_{row.get('Description', '')}_{row.get('Member Name', '')}"
                    dedup_key = hashlib.md5(fingerprint_data.encode()).hexdigest()

                    # Check for duplicates
                    existing = await self.db.transactions_raw.find_one({
                        "source_bank": "citi",
                        "dedup_key": dedup_key
                    })

                    if existing:
                        skipped_duplicates += 1
                        print(f"⏭️  Skipping duplicate (row {row_num}): {row.get('Description', '')[:30]}...")
                        continue

                    # Store transaction_type in raw_data for enricher
                    row_with_type = dict(row)
                    row_with_type['_transaction_type'] = transaction_type
                    row_with_type['_amount'] = amount

                    # Create TransactionRaw document
                    transaction = TransactionRaw(
                        source_bank="citi",
                        import_id=self.import_id,
                        raw_data=row_with_type,
                        file_name=self.file_name,
                        created_at=datetime.utcnow(),
                        processed=False,
                        raw_text=raw_text,
                        dedup_key=dedup_key,
                        dedup_method="fingerprint",
                    )

                    # Insert into MongoDB
                    await self.db.transactions_raw.insert_one(transaction.model_dump())
                    successful_rows += 1

                except Exception as e:
                    errors.append({
                        "row_number": row_num,
                        "message": str(e),
                        "timestamp": datetime.utcnow(),
                    })
                    print(f"Error parsing row {row_num}: {e}")

        return {
            "total_rows": total_rows,
            "successful_rows": successful_rows,
            "skipped_duplicates": skipped_duplicates,
            "failed_rows": len(errors),
            "errors": errors,
        }
