from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import connect_to_mongo, close_mongo_connection
from app.api.v1 import imports, transactions, balances, merchants


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()


app = FastAPI(
    title="Guppy Funds API",
    description="""
## Personal Finance Ingestion and Enrichment Service

Automated system for importing, processing, and enriching financial transactions from multiple banks.

### Features
- **Multi-Bank Support**: AMEX, Citi, Wells Fargo
- **AI-Powered Enrichment**: Claude API for merchant normalization and categorization
- **Duplicate Detection**: Intelligent deduplication across uploads
- **Merchant Caching**: Reuses enrichment results for cost optimization
- **Automated Processing**: Background worker handles everything

### Quick Start
1. Upload CSV: `POST /v1/imports`
2. Wait 30-60 seconds for automatic processing
3. Query enriched data: `GET /v1/transactions`

### Transaction Types
- **income**: Payroll, direct deposits, salary
- **debit**: Spending (purchases, bills, fees)
- **credit**: Refunds, credits from merchants
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc UI
    openapi_url="/openapi.json",  # OpenAPI schema
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(imports.router)
app.include_router(transactions.router)
app.include_router(balances.router)
app.include_router(merchants.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Guppy Funds API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check for monitoring."""
    return {"status": "healthy"}
