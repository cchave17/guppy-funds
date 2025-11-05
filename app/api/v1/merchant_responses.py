"""Response schemas for merchant and category endpoints."""

from typing import List, Optional
from pydantic import BaseModel, Field


class MerchantListItem(BaseModel):
    """Merchant item in list response."""

    merchant_id: str
    name: str
    category: Optional[str]
    subcategory: Optional[str]
    is_subscription: bool
    transaction_count: int = 0
    total_spent: float = 0.0
    aliases: List[str] = []


class MerchantListResponse(BaseModel):
    """Response for /v1/merchants endpoint."""

    merchants: List[MerchantListItem]
    total_count: int
    limit: int

    class Config:
        json_schema_extra = {
            "example": {
                "merchants": [
                    {
                        "merchant_id": "amazon-marketplace",
                        "name": "Amazon Marketplace",
                        "category": "Shopping",
                        "subcategory": "Online Retail",
                        "is_subscription": False,
                        "transaction_count": 12,
                        "total_spent": 567.89,
                        "aliases": ["AMAZON MARKETPLACE NA", "AMZN.COM"],
                    }
                ],
                "total_count": 65,
                "limit": 50,
            }
        }


class MerchantStats(BaseModel):
    """Statistics for a merchant."""

    transaction_count: int
    total_spent: float
    average_transaction: float
    first_transaction: str
    last_transaction: str


class MerchantDetailResponse(BaseModel):
    """Detailed merchant response."""

    merchant_id: str
    name: str
    category: Optional[str]
    subcategory: Optional[str]
    tags: List[str]
    is_subscription: bool
    aliases: List[str]
    statistics: MerchantStats

    class Config:
        json_schema_extra = {
            "example": {
                "merchant_id": "amazon-marketplace",
                "name": "Amazon Marketplace",
                "category": "Shopping",
                "subcategory": "Online Retail",
                "tags": ["amazon", "ecommerce", "online"],
                "is_subscription": False,
                "aliases": ["AMAZON MARKETPLACE NA", "AMZN.COM/BILL WA"],
                "statistics": {
                    "transaction_count": 12,
                    "total_spent": 567.89,
                    "average_transaction": 47.32,
                    "first_transaction": "2025-09-15",
                    "last_transaction": "2025-10-25",
                },
            }
        }


class CategoryItem(BaseModel):
    """Category with stats."""

    category: str
    total: float
    count: int
    percentage: float
    average_transaction: float


class CategoriesResponse(BaseModel):
    """Response for /v1/categories endpoint."""

    categories: List[CategoryItem]
    total_expenses: float
    period: str

    class Config:
        json_schema_extra = {
            "example": {
                "categories": [
                    {
                        "category": "Groceries",
                        "total": 800.0,
                        "count": 25,
                        "percentage": 22.8,
                        "average_transaction": 32.0,
                    }
                ],
                "total_expenses": 3500.0,
                "period": "current_month",
            }
        }
