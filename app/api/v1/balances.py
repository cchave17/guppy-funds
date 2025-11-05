"""Balance query endpoints."""

from typing import Literal
from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from app.database import get_database
from app.api.v1.balance_responses import (
    BalancesResponse,
    SingleBankBalanceResponse,
    BalancesSummary,
)


router = APIRouter(
    prefix="/v1/balances",
    tags=["Balances"],
)


@router.get(
    "",
    response_model=BalancesResponse,
    summary="Get all account balances",
    description="""
    Get current balance for all accounts with net worth calculation.

    **Balance Calculations:**
    - **Wells Fargo (Checking)**: Income - Expenses = Cash on hand
    - **AMEX/Citi (Credit Cards)**: Charges - Payments = Amount owed (negative = debt)
    - **Net Worth**: Total cash - Total debt

    **Note:** Balances are calculated from all transactions in the database.
    """,
)
async def get_balances():
    """Get balances for all accounts."""
    db = get_database()

    accounts = {}
    total_cash = 0.0
    total_debt = 0.0

    # Calculate for each bank
    for bank in ["wells", "amex", "citi"]:
        bank_filter = {"source_bank": bank}

        if bank == "wells":
            # Checking account: income - expenses
            income_result = await db.transactions_enriched.aggregate([
                {"$match": {**bank_filter, "type": "income"}},
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": "$amount"},
                        "last_date": {"$max": "$date"},
                    }
                },
            ]).to_list(1)

            expenses_result = await db.transactions_enriched.aggregate([
                {"$match": {**bank_filter, "type": "debit"}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
            ]).to_list(1)

            income = income_result[0]["total"] if income_result else 0.0
            expenses = expenses_result[0]["total"] if expenses_result else 0.0
            last_date = (
                income_result[0]["last_date"] if income_result else datetime.utcnow()
            )
            running_balance = income - expenses

            accounts[bank] = {
                "name": "Wells Fargo Checking",
                "type": "checking",
                "running_balance": running_balance,
                "income_total": income,
                "expenses_total": expenses,
                "last_transaction_date": last_date.strftime("%Y-%m-%d"),
            }

            total_cash += running_balance

        else:
            # Credit cards: charges - payments
            charges_result = await db.transactions_enriched.aggregate([
                {"$match": {**bank_filter, "type": "debit"}},
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": "$amount"},
                        "last_date": {"$max": "$date"},
                    }
                },
            ]).to_list(1)

            payments_result = await db.transactions_enriched.aggregate([
                {"$match": {**bank_filter, "type": "credit"}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
            ]).to_list(1)

            charges = charges_result[0]["total"] if charges_result else 0.0
            payments = payments_result[0]["total"] if payments_result else 0.0
            last_date = (
                charges_result[0]["last_date"]
                if charges_result
                else datetime.utcnow()
            )
            amount_owed = -(charges - payments)  # Negative = debt

            bank_name = (
                "American Express" if bank == "amex" else "Citi Costco Visa"
            )

            accounts[bank] = {
                "name": bank_name,
                "type": "credit_card",
                "amount_owed": amount_owed,
                "charges": charges,
                "payments": payments,
                "last_transaction_date": last_date.strftime("%Y-%m-%d"),
            }

            total_debt += amount_owed

    return BalancesResponse(
        as_of_date=datetime.utcnow().strftime("%Y-%m-%d"),
        accounts=accounts,
        summary=BalancesSummary(
            total_cash=total_cash,
            total_debt=total_debt,
            net_worth=total_cash + total_debt,  # debt is negative
        ),
    )


@router.get(
    "/{source_bank}",
    response_model=SingleBankBalanceResponse,
    summary="Get balance for specific bank",
    description="""
    Get balance for a specific bank account.

    **Supported Banks:**
    - `wells` - Wells Fargo Checking
    - `amex` - American Express
    - `citi` - Citi Costco Visa
    """,
)
async def get_bank_balance(source_bank: Literal["wells", "amex", "citi"]):
    """Get balance for a specific bank."""
    db = get_database()

    bank_filter = {"source_bank": source_bank}

    if source_bank == "wells":
        # Checking account
        income_result = await db.transactions_enriched.aggregate([
            {"$match": {**bank_filter, "type": "income"}},
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$amount"},
                    "last_date": {"$max": "$date"},
                }
            },
        ]).to_list(1)

        expenses_result = await db.transactions_enriched.aggregate([
            {"$match": {**bank_filter, "type": "debit"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
        ]).to_list(1)

        income = income_result[0]["total"] if income_result else 0.0
        expenses = expenses_result[0]["total"] if expenses_result else 0.0
        last_date = (
            income_result[0]["last_date"].strftime("%Y-%m-%d")
            if income_result
            else datetime.utcnow().strftime("%Y-%m-%d")
        )

        return SingleBankBalanceResponse(
            source_bank=source_bank,
            name="Wells Fargo Checking",
            type="checking",
            balance=income - expenses,
            breakdown={
                "income": income,
                "expenses": expenses,
                "net": income - expenses,
            },
            last_transaction_date=last_date,
        )

    else:
        # Credit card
        charges_result = await db.transactions_enriched.aggregate([
            {"$match": {**bank_filter, "type": "debit"}},
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$amount"},
                    "last_date": {"$max": "$date"},
                }
            },
        ]).to_list(1)

        payments_result = await db.transactions_enriched.aggregate([
            {"$match": {**bank_filter, "type": "credit"}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
        ]).to_list(1)

        charges = charges_result[0]["total"] if charges_result else 0.0
        payments = payments_result[0]["total"] if payments_result else 0.0
        last_date = (
            charges_result[0]["last_date"].strftime("%Y-%m-%d")
            if charges_result
            else datetime.utcnow().strftime("%Y-%m-%d")
        )

        bank_name = "American Express" if source_bank == "amex" else "Citi Costco Visa"

        return SingleBankBalanceResponse(
            source_bank=source_bank,
            name=bank_name,
            type="credit_card",
            balance=-(charges - payments),  # Negative = debt
            breakdown={
                "charges": charges,
                "payments": payments,
                "amount_owed": -(charges - payments),
            },
            last_transaction_date=last_date,
        )
