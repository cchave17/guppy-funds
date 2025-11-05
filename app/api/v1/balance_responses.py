"""Response schemas for balance endpoints."""

from typing import Dict, Any
from pydantic import BaseModel, Field


class CheckingAccountBalance(BaseModel):
    """Balance for checking/debit accounts (Wells Fargo)."""

    name: str
    type: str = "checking"
    running_balance: float = Field(..., description="Current balance (income - expenses)")
    income_total: float
    expenses_total: float
    last_transaction_date: str


class CreditCardBalance(BaseModel):
    """Balance for credit card accounts (AMEX, Citi)."""

    name: str
    type: str = "credit_card"
    amount_owed: float = Field(
        ..., description="Amount owed (negative = debt, positive = credit)"
    )
    charges: float
    payments: float
    last_transaction_date: str


class BalancesSummary(BaseModel):
    """Summary of all balances."""

    total_cash: float = Field(..., description="Total cash in checking accounts")
    total_debt: float = Field(..., description="Total credit card debt (negative)")
    net_worth: float = Field(..., description="Cash - Debt")


class BalancesResponse(BaseModel):
    """Response for /v1/balances endpoint."""

    as_of_date: str
    accounts: Dict[str, Dict[str, Any]]
    summary: BalancesSummary

    class Config:
        json_schema_extra = {
            "example": {
                "as_of_date": "2025-10-28",
                "accounts": {
                    "wells": {
                        "name": "Wells Fargo Checking",
                        "type": "checking",
                        "running_balance": 3500.0,
                        "income_total": 8000.0,
                        "expenses_total": 4500.0,
                        "last_transaction_date": "2025-10-27",
                    },
                    "amex": {
                        "name": "American Express",
                        "type": "credit_card",
                        "amount_owed": -2000.0,
                        "charges": 2000.0,
                        "payments": 0.0,
                        "last_transaction_date": "2025-10-25",
                    },
                    "citi": {
                        "name": "Citi Costco Visa",
                        "type": "credit_card",
                        "amount_owed": -1000.0,
                        "charges": 1000.0,
                        "payments": 0.0,
                        "last_transaction_date": "2025-10-24",
                    },
                },
                "summary": {
                    "total_cash": 3500.0,
                    "total_debt": -3000.0,
                    "net_worth": 500.0,
                },
            }
        }


class SingleBankBalanceResponse(BaseModel):
    """Response for /v1/balances/{source_bank} endpoint."""

    source_bank: str
    name: str
    type: str  # "checking" or "credit_card"
    balance: float
    breakdown: Dict[str, float]
    last_transaction_date: str

    class Config:
        json_schema_extra = {
            "example": {
                "source_bank": "wells",
                "name": "Wells Fargo Checking",
                "type": "checking",
                "balance": 3500.0,
                "breakdown": {
                    "income": 8000.0,
                    "expenses": 4500.0,
                    "net": 3500.0,
                },
                "last_transaction_date": "2025-10-27",
            }
        }
