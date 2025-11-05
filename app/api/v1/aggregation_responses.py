"""Response schemas for aggregation endpoints."""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class PeriodInfo(BaseModel):
    """Period information for aggregation results."""

    start: str
    end: str
    type: str  # "current_month", "last_30_days", etc.


class TotalsSummary(BaseModel):
    """Total income/expenses summary."""

    income: float
    expenses: float
    net: float
    transaction_count: int


class BankSummary(BaseModel):
    """Bank-specific summary (for checking accounts like Wells)."""

    income: float = 0.0
    expenses: float = 0.0
    net: float = 0.0
    running_balance: float = 0.0


class CreditCardSummary(BaseModel):
    """Credit card summary (for AMEX/Citi)."""

    expenses: float = 0.0
    payments: float = 0.0
    amount_owed: float = 0.0  # Negative indicates debt


class CategorySummaryItem(BaseModel):
    """Category summary for top categories."""

    category: str
    total: float
    count: int


class TransactionSummaryResponse(BaseModel):
    """Response for /summary endpoint."""

    period: PeriodInfo
    totals: TotalsSummary
    by_bank: Dict[str, Dict[str, float]]
    top_categories: List[CategorySummaryItem]

    class Config:
        json_schema_extra = {
            "example": {
                "period": {
                    "start": "2025-10-01",
                    "end": "2025-10-31",
                    "type": "current_month",
                },
                "totals": {
                    "income": 7923.35,
                    "expenses": 5234.67,
                    "net": 2688.68,
                    "transaction_count": 152,
                },
                "by_bank": {
                    "wells": {
                        "income": 7923.35,
                        "expenses": 1234.56,
                        "net": 6688.79,
                        "running_balance": 6688.79,
                    },
                    "amex": {"expenses": 2500.0, "payments": 0.0, "amount_owed": -2500.0},
                    "citi": {"expenses": 1500.11, "payments": 0.0, "amount_owed": -1500.11},
                },
                "top_categories": [
                    {"category": "Groceries", "total": 800.0, "count": 25},
                    {"category": "Restaurants", "total": 650.0, "count": 18},
                ],
            }
        }


class SubcategoryBreakdown(BaseModel):
    """Subcategory breakdown."""

    name: str
    total: float
    count: int


class CategoryDetail(BaseModel):
    """Detailed category breakdown."""

    category: str
    total: float
    count: int
    percentage: float
    average_transaction: float
    subcategories: List[SubcategoryBreakdown] = []


class ByCategoryResponse(BaseModel):
    """Response for /by-category endpoint."""

    period: str
    total_expenses: float
    categories: List[CategoryDetail]

    class Config:
        json_schema_extra = {
            "example": {
                "period": "current_month",
                "total_expenses": 3500.0,
                "categories": [
                    {
                        "category": "Groceries",
                        "total": 800.0,
                        "count": 25,
                        "percentage": 22.8,
                        "average_transaction": 32.0,
                        "subcategories": [
                            {"name": "Supermarket", "total": 600.0, "count": 18}
                        ],
                    }
                ],
            }
        }


class MerchantSummary(BaseModel):
    """Merchant summary with transaction stats."""

    merchant_id: str
    merchant_name: str
    category: Optional[str]
    is_subscription: bool
    total_spent: float
    transaction_count: int
    average_transaction: float
    first_transaction: str
    last_transaction: str


class ByMerchantResponse(BaseModel):
    """Response for /by-merchant endpoint."""

    period: str
    total_count: int
    merchants: List[MerchantSummary]
    limit: int

    class Config:
        json_schema_extra = {
            "example": {
                "period": "current_month",
                "total_count": 65,
                "merchants": [
                    {
                        "merchant_id": "amazon-marketplace",
                        "merchant_name": "Amazon Marketplace",
                        "category": "Shopping",
                        "is_subscription": False,
                        "total_spent": 567.89,
                        "transaction_count": 12,
                        "average_transaction": 47.32,
                        "first_transaction": "2025-10-05",
                        "last_transaction": "2025-10-28",
                    }
                ],
                "limit": 20,
            }
        }


class MonthSummary(BaseModel):
    """Monthly summary."""

    month: str  # "2025-10"
    year: int
    income: float
    expenses: float
    net: float
    transaction_count: int
    top_category: Optional[str] = None


class ByMonthResponse(BaseModel):
    """Response for /by-month endpoint."""

    range: str
    months: List[MonthSummary]

    class Config:
        json_schema_extra = {
            "example": {
                "range": "last_12_months",
                "months": [
                    {
                        "month": "2025-10",
                        "year": 2025,
                        "income": 7923.35,
                        "expenses": 5234.67,
                        "net": 2688.68,
                        "transaction_count": 152,
                        "top_category": "Groceries",
                    }
                ],
            }
        }
