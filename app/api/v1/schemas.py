"""Response schemas for API documentation."""

from typing import Optional, List
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Response for successful file upload."""

    import_id: str = Field(..., description="Unique identifier for the import job")
    state: str = Field(..., description="Current state of the import")
    message: str = Field(..., description="Human-readable status message")

    class Config:
        json_schema_extra = {
            "example": {
                "import_id": "import_2025_10_28_131943",
                "state": "uploaded",
                "message": "File accepted. Import queued for processing.",
            }
        }


class ParseResponse(BaseModel):
    """Response for parsing completion."""

    import_id: str
    state: str
    total_rows: int = Field(..., description="Total rows in CSV")
    parsed_rows: int = Field(..., description="Successfully parsed rows")
    failed_rows: int = Field(..., description="Failed rows")
    duration_ms: int = Field(..., description="Parsing duration in milliseconds")
    message: str


class EnrichResponse(BaseModel):
    """Response for enrichment completion."""

    import_id: str
    state: str
    enriched_rows: int = Field(..., description="Successfully enriched rows")
    failed_rows: int = Field(..., description="Failed rows")
    duration_ms: int = Field(..., description="Enrichment duration in milliseconds")
    message: str


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: dict = Field(
        ...,
        description="Error details",
        examples=[
            {
                "code": "IMPORT_FAILED",
                "message": "Parsing failed due to malformed CSV",
                "details": {"line": 12, "reason": "missing column"},
            }
        ],
    )
