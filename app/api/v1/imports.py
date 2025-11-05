import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse

from app.database import get_database
from app.models import Import, ImportState
from app.config import settings
from app.parsers.amex_parser import AmexParser
from app.parsers.citi_parser import CitiParser
from app.parsers.wells_parser import WellsParser
from app.enrichers.claude_enricher import ClaudeEnricher
from app.api.v1.schemas import UploadResponse, ParseResponse, EnrichResponse

router = APIRouter(
    prefix="/v1/imports",
    tags=["Import Management"],
    responses={404: {"description": "Import not found"}},
)


def generate_import_id() -> str:
    """Generate unique import ID with timestamp."""
    now = datetime.utcnow()
    return f"import_{now.year}_{now.month:02d}_{now.day:02d}_{now.hour:02d}{now.minute:02d}{now.second:02d}"


def calculate_checksum(file_path: str) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=UploadResponse,
    summary="Upload CSV file",
    description="""
    Upload a financial CSV file for processing.

    **Supported Banks:**
    - `amex` - American Express
    - `citi` - Citi Bank (Costco Visa)
    - `wells` - Wells Fargo

    **What Happens:**
    1. File is validated and saved
    2. Import record created with state "uploaded"
    3. Background worker automatically parses and enriches
    4. Process completes in 30-60 seconds

    **Duplicate Protection:**
    - Uploading the same file multiple times will skip duplicate transactions
    - Safe to upload overlapping monthly statements
    """,
)
async def upload_import(
    file: UploadFile = File(..., description="CSV file from your bank"),
    source_bank: Literal["amex", "citi", "wells"] = Form(
        ..., description="Bank source: amex, citi, or wells"
    ),
):
    """Upload a CSV file and create a new import job."""
    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are accepted",
        )

    # Check file size (convert MB to bytes)
    max_size_bytes = settings.max_file_size_mb * 1024 * 1024
    file_content = await file.read()

    if len(file_content) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum of {settings.max_file_size_mb}MB",
        )

    # Reset file pointer after reading
    await file.seek(0)

    # Generate import ID and prepare storage
    import_id = generate_import_id()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save file with unique name
    file_path = upload_dir / f"{import_id}_{file.filename}"

    try:
        # Write file to disk
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Calculate checksum
        checksum = calculate_checksum(str(file_path))

        # Create import record
        import_doc = Import(
            import_id=import_id,
            source_bank=source_bank,
            file_name=file.filename,
            file_path=str(file_path),
            upload_time=datetime.utcnow(),
            state=ImportState.UPLOADED,
            checksum=checksum,
        )

        # Store in MongoDB
        db = get_database()
        await db.imports.insert_one(import_doc.model_dump())

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "import_id": import_id,
                "state": ImportState.UPLOADED.value,
                "message": "File accepted. Import queued for processing.",
            },
        )

    except Exception as e:
        # Clean up file if database insert fails
        if file_path.exists():
            os.remove(file_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process upload: {str(e)}",
        )


@router.post(
    "/{import_id}/parse",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ParseResponse,
    summary="Manually trigger parsing",
    description="""
    Manually trigger CSV parsing (normally handled by worker).

    Converts CSV rows into structured transactions in the `transactions_raw` collection.
    """,
)
async def parse_import(import_id: str):
    """Parse a CSV file and populate transactions_raw collection."""
    db = get_database()

    # Find the import
    import_doc = await db.imports.find_one({"import_id": import_id})

    if not import_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import {import_id} not found",
        )

    # Check if already parsed
    if import_doc["state"] not in [ImportState.UPLOADED.value, ImportState.FAILED.value]:
        return JSONResponse(
            content={
                "import_id": import_id,
                "state": import_doc["state"],
                "message": f"Import already in state: {import_doc['state']}",
            }
        )

    # Update state to parsing
    start_time = datetime.utcnow()
    await db.imports.update_one(
        {"import_id": import_id},
        {
            "$set": {
                "state": ImportState.PARSING.value,
                "started_at": start_time,
            }
        },
    )

    try:
        # Parse based on source_bank
        source_bank = import_doc["source_bank"]

        if source_bank == "amex":
            parser = AmexParser(
                file_path=import_doc["file_path"],
                import_id=import_id,
                file_name=import_doc["file_name"],
                db=db,
            )
        elif source_bank == "citi":
            parser = CitiParser(
                file_path=import_doc["file_path"],
                import_id=import_id,
                file_name=import_doc["file_name"],
                db=db,
            )
        elif source_bank == "wells":
            parser = WellsParser(
                file_path=import_doc["file_path"],
                import_id=import_id,
                file_name=import_doc["file_name"],
                db=db,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parser for {source_bank} not yet implemented",
            )

        # Run parser
        result = await parser.parse()

        # Calculate duration
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # Update import with results
        await db.imports.update_one(
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

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "import_id": import_id,
                "state": ImportState.PARSED.value,
                "total_rows": result["total_rows"],
                "parsed_rows": result["successful_rows"],
                "failed_rows": result["failed_rows"],
                "duration_ms": duration_ms,
                "message": "Parsing completed successfully",
            },
        )

    except Exception as e:
        # Mark as failed
        await db.imports.update_one(
            {"import_id": import_id},
            {
                "$set": {
                    "state": ImportState.FAILED.value,
                    "notes": f"Parsing failed: {str(e)}",
                    "completed_at": datetime.utcnow(),
                }
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Parsing failed: {str(e)}",
        )


@router.post(
    "/{import_id}/enrich",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=EnrichResponse,
    summary="Manually trigger enrichment",
    description="""
    Manually trigger AI enrichment (normally handled by worker).

    Uses Claude API to:
    - Normalize merchant names
    - Assign categories and subcategories
    - Extract location data
    - Detect subscriptions and income
    - Generate relevant tags

    Results are cached in the `merchants` collection for future reuse.
    """,
)
async def enrich_import(import_id: str):
    """Enrich parsed transactions using Claude API."""
    db = get_database()

    # Find the import
    import_doc = await db.imports.find_one({"import_id": import_id})

    if not import_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import {import_id} not found",
        )

    # Check if already enriched
    if import_doc["state"] not in [
        ImportState.PARSED.value,
        ImportState.FAILED.value,
    ]:
        if import_doc["state"] == ImportState.UPLOADED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Import must be parsed before enrichment. Call /parse first.",
            )
        return JSONResponse(
            content={
                "import_id": import_id,
                "state": import_doc["state"],
                "message": f"Import already in state: {import_doc['state']}",
            }
        )

    # Update state to enriching
    start_time = datetime.utcnow()
    await db.imports.update_one(
        {"import_id": import_id},
        {
            "$set": {
                "state": ImportState.ENRICHING.value,
                "started_at": start_time,
            }
        },
    )

    try:
        # Create enricher and run enrichment
        enricher = ClaudeEnricher(import_id=import_id, db=db)
        result = await enricher.enrich_import()

        # Calculate duration
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # Update import with results
        await db.imports.update_one(
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
        await db.imports.update_one(
            {"import_id": import_id}, {"$set": {"state": ImportState.COMPLETED.value}}
        )

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "import_id": import_id,
                "state": ImportState.COMPLETED.value,
                "enriched_rows": result["successful_rows"],
                "failed_rows": result["failed_rows"],
                "duration_ms": duration_ms,
                "message": "Enrichment completed successfully",
            },
        )

    except Exception as e:
        # Mark as failed
        await db.imports.update_one(
            {"import_id": import_id},
            {
                "$set": {
                    "state": ImportState.FAILED.value,
                    "notes": f"Enrichment failed: {str(e)}",
                    "completed_at": datetime.utcnow(),
                }
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrichment failed: {str(e)}",
        )
