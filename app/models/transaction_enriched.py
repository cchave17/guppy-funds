from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Location(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class MerchantInfo(BaseModel):
    name: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    location: Optional[Location] = None


class AccountInfo(BaseModel):
    name: str
    account_number: Optional[str] = None
    card_member: Optional[str] = None


class TransactionEnriched(BaseModel):
    transaction_id: str  # UUID or generated ID
    source_bank: str
    import_id: str
    raw_id: str  # Reference to original document in transactions_raw
    enrichment_version: float = 1.0
    date: datetime
    description: str
    amount: float  # Always positive
    type: str  # "debit" | "credit" | "income"
    currency: str = "USD"
    merchant: MerchantInfo
    account: AccountInfo
    tags: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
    is_recurring: bool = False
    enriched_confidence: float = 0.0  # 0-1 confidence score
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "7e2b21c0-27af-4a9e-bb40-88b81cdd9f95",
                "source_bank": "amex",
                "import_id": "import_2025_10_28_1",
                "raw_id": "671ebd5c2a0fdc002ab2fa6d",
                "enrichment_version": 1.0,
                "date": "2025-10-25T00:00:00Z",
                "description": "AMAZON MARKETPLACE NA",
                "amount": 77.04,
                "type": "debit",
                "currency": "USD",
                "merchant": {
                    "name": "Amazon Marketplace",
                    "category": "Shopping",
                    "subcategory": "Online Retail",
                },
                "account": {"name": "AMEX Platinum", "card_member": "Carlos Y Chavez"},
                "tags": ["shopping", "amazon"],
                "is_recurring": False,
                "enriched_confidence": 0.98,
            }
        }
