import csv
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.models import TransactionRaw


class WellsParser:
    """Parser for Wells Fargo CSV files (no headers)."""

    def __init__(self, file_path: str, import_id: str, file_name: str, db=None):
        self.file_path = Path(file_path)
        self.import_id = import_id
        self.file_name = file_name
        self.db = db

    async def parse(self) -> dict:
        """
        Parse Wells Fargo CSV and insert into transactions_raw collection.
        Wells CSVs have NO HEADERS - we manually map columns.
        Uses fingerprint-based duplicate detection.

        Column mapping:
        0: Date
        1: Amount (negative = debit, positive = credit)
        2-3: Unknown/flags
        4: Transaction Type/Description (full text)

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
            # No headers - read as plain CSV
            reader = csv.reader(file)

            for row_num, row in enumerate(reader, start=1):
                try:
                    # Skip if not enough columns
                    if len(row) < 5:
                        continue

                    total_rows += 1

                    # Map columns manually
                    date = row[0].strip()
                    amount_str = row[1].strip()
                    flag1 = row[2].strip()
                    flag2 = row[3].strip()
                    description = row[4].strip()

                    # Parse amount and determine type
                    amount = float(amount_str)
                    if amount < 0:
                        transaction_type = "debit"
                        abs_amount = abs(amount)
                    else:
                        transaction_type = "credit"
                        abs_amount = amount

                    # Create structured raw_data
                    raw_data = {
                        "Date": date,
                        "Amount": amount_str,
                        "Transaction Type": description,
                        "Notes": f"{flag1} {flag2}".strip() if flag1 or flag2 else None,
                        "_transaction_type": transaction_type,
                        "_amount": abs_amount,
                    }

                    # Create raw_text
                    raw_text = f"{date}, {amount_str}, {description}"

                    # Generate fingerprint for deduplication
                    # Using: date + amount + first 50 chars of description
                    fingerprint_data = f"wells_{date}_{amount_str}_{description[:50]}"
                    dedup_key = hashlib.md5(fingerprint_data.encode()).hexdigest()

                    # Check for duplicates
                    existing = await self.db.transactions_raw.find_one({
                        "source_bank": "wells",
                        "dedup_key": dedup_key
                    })

                    if existing:
                        skipped_duplicates += 1
                        print(f"⏭️  Skipping duplicate (row {row_num}): {description[:30]}...")
                        continue

                    # Create TransactionRaw document
                    transaction = TransactionRaw(
                        source_bank="wells",
                        import_id=self.import_id,
                        raw_data=raw_data,
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
