from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ImportState(str, Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    ENRICHING = "enriching"
    ENRICHED = "enriched"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportError(BaseModel):
    row_number: int
    message: str
    timestamp: datetime


class Import(BaseModel):
    import_id: str
    source_bank: str  # "amex" | "citi" | "wells"
    file_name: str
    file_path: str
    upload_time: datetime
    state: ImportState = ImportState.UPLOADED
    total_rows: int = 0
    parsed_rows: int = 0
    enriched_rows: int = 0
    failed_rows: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    errors: list[ImportError] = Field(default_factory=list)
    enrichment_version: Optional[float] = None
    notes: Optional[str] = None
    checksum: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "import_id": "import_2025_10_28_1",
                "source_bank": "amex",
                "file_name": "AMEX.csv",
                "file_path": "/uploads/AMEX.csv",
                "upload_time": "2025-10-28T12:00:00Z",
                "state": "uploaded",
                "total_rows": 0,
                "parsed_rows": 0,
                "enriched_rows": 0,
            }
        }
