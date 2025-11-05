import csv
from datetime import datetime
from pathlib import Path
from typing import Optional


from app.models import TransactionRaw


class AmexParser:
    """Parser for AMEX CSV files."""

    def __init__(self, file_path: str, import_id: str, file_name: str, db=None):
        self.file_path = Path(file_path)
        self.import_id = import_id
        self.file_name = file_name
        self.db = db

    async def parse(self) -> dict:
        """
        Parse AMEX CSV and insert into transactions_raw collection.
        Includes duplicate detection using Reference field.

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
            # Use csv.DictReader to handle multiline fields properly
            reader = csv.DictReader(file)

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                try:
                    total_rows += 1

                    # Create raw_text (concatenate key fields for LLM enrichment)
                    raw_text = f"{row.get('Date', '')}, {row.get('Description', '')}, {row.get('Amount', '')}, {row.get('Category', '')}"

                    # Clean up the Reference field (remove single quotes if present)
                    reference = row.get('Reference', '').strip("'") if row.get('Reference') else None
                    if reference and 'Reference' in row:
                        row['Reference'] = reference

                    # Generate dedup_key using AMEX Reference field
                    dedup_key = reference if reference else f"amex_{row.get('Date')}_{row.get('Amount')}_{row.get('Description', '')[:20]}"
                    dedup_method = "reference" if reference else "fallback"

                    # Check for duplicates
                    existing = await self.db.transactions_raw.find_one({
                        "source_bank": "amex",
                        "dedup_key": dedup_key
                    })

                    if existing:
                        skipped_duplicates += 1
                        print(f"⏭️  Skipping duplicate (row {row_num}): {dedup_key[:20]}...")
                        continue  # Skip this transaction

                    # Create TransactionRaw document
                    transaction = TransactionRaw(
                        source_bank="amex",
                        import_id=self.import_id,
                        raw_data=dict(row),  # Store all CSV columns
                        file_name=self.file_name,
                        created_at=datetime.utcnow(),
                        processed=False,
                        raw_text=raw_text,
                        dedup_key=dedup_key,
                        dedup_method=dedup_method,
                    )

                    # Insert into MongoDB
                    await self.db.transactions_raw.insert_one(transaction.model_dump())
                    successful_rows += 1

                except Exception as e:
                    error_msg = f"Row {row_num}: {str(e)}"
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
