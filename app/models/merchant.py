from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    support_url: Optional[str] = None


class MerchantLocation(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class Merchant(BaseModel):
    merchant_id: str  # UUID or normalized slug
    name: str  # Canonical merchant name
    aliases: list[str] = Field(default_factory=list)
    category: Optional[str] = None
    subcategory: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    website: Optional[str] = None
    contact_info: Optional[ContactInfo] = None
    location: Optional[MerchantLocation] = None
    is_subscription: bool = False  # True for recurring subscription services
    enrichment_confidence: float = 0.0
    enrichment_version: float = 1.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "merchant_id": "amazon-marketplace",
                "name": "Amazon Marketplace",
                "aliases": ["AMAZON MARKETPLACE NA", "AMZN.COM/BILL WA"],
                "category": "Shopping",
                "subcategory": "Online Retail",
                "tags": ["amazon", "ecommerce"],
                "website": "https://www.amazon.com",
                "enrichment_confidence": 0.97,
            }
        }
