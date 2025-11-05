"""Response schemas for transaction endpoints."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MerchantResponse(BaseModel):
    """Merchant information in transaction response."""

    name: str
    category: Optional[str] = None
    subcategory: Optional[str] = None


class AccountResponse(BaseModel):
    """Account information in transaction response."""

    name: str
    card_member: Optional[str] = None


class TransactionResponse(BaseModel):
    """Single transaction in list response."""

    transaction_id: str
    date: datetime
    description: str
    amount: float
    type: str  # "debit" | "credit" | "income"
    source_bank: str
    merchant: MerchantResponse
    account: AccountResponse
    tags: List[str] = []
    is_recurring: bool = False
    category: Optional[str] = None  # Shortcut to merchant.category


class TransactionListResponse(BaseModel):
    """Response for transaction list queries."""

    transactions: List[TransactionResponse]
    total_count: int = Field(..., description="Total matching transactions (ignoring pagination)")
    limit: int
    offset: int
    has_more: bool = Field(..., description="Whether more results are available")
    filters_applied: Dict[str, Any] = Field(
        default_factory=dict, description="Summary of applied filters"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "transactions": [
                    {
                        "transaction_id": "abc-123",
                        "date": "2025-10-25T00:00:00Z",
                        "description": "Amazon Marketplace",
                        "amount": 77.04,
                        "type": "debit",
                        "source_bank": "amex",
                        "merchant": {
                            "name": "Amazon Marketplace",
                            "category": "Shopping",
                            "subcategory": "Online Retail",
                        },
                        "account": {"name": "AMEX 91016", "card_member": "Carlos Chavez"},
                        "tags": ["amazon", "ecommerce"],
                        "is_recurring": False,
                        "category": "Shopping",
                    }
                ],
                "total_count": 150,
                "limit": 50,
                "offset": 0,
                "has_more": True,
                "filters_applied": {"period": "current_month", "type": "debit"},
            }
        }


class TransactionDetailResponse(BaseModel):
    """Detailed single transaction response."""

    transaction_id: str
    date: datetime
    description: str
    amount: float
    type: str
    currency: str
    source_bank: str
    merchant: Dict[str, Any]
    account: Dict[str, Any]
    tags: List[str]
    is_recurring: bool
    enriched_confidence: float
    raw_id: str
    import_id: str
    created_at: datetime
    updated_at: datetime
