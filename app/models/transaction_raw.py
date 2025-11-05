from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class TransactionRaw(BaseModel):
    source_bank: str  # "amex" | "citi" | "wells"
    import_id: str
    raw_data: dict[str, Any]  # Original CSV row as key:value pairs
    file_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = False
    notes: Optional[str] = None
    raw_text: str  # Concatenated line of original CSV row
    dedup_key: str  # Unique identifier for duplicate detection
    dedup_method: str  # "reference" for AMEX, "fingerprint" for others

    class Config:
        json_schema_extra = {
            "example": {
                "source_bank": "amex",
                "import_id": "import_2025_10_28_1",
                "file_name": "AMEX.csv",
                "created_at": "2025-10-28T12:00:00Z",
                "processed": False,
                "raw_text": "10/25/2025, AMAZON MARKETPLACE NA, 77.04, Merchandise & Supplies-Internet Purchase",
                "raw_data": {
                    "Date": "10/25/2025",
                    "Description": "AMAZON MARKETPLACE NA",
                    "Amount": 77.04,
                    "Category": "Merchandise & Supplies-Internet Purchase",
                },
            }
        }
