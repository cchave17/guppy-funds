"""Merchant and category query endpoints."""

from typing import Optional, Literal

from fastapi import APIRouter, Query, HTTPException, status

from app.database import get_database
from app.api.v1.merchant_responses import (
    MerchantListResponse,
    MerchantListItem,
    MerchantDetailResponse,
    MerchantStats,
    CategoriesResponse,
    CategoryItem,
)
from app.api.v1.transaction_responses import TransactionListResponse, TransactionResponse, MerchantResponse, AccountResponse
from app.utils.date_helpers import get_date_range, format_period_name, DatePeriod


router = APIRouter(tags=["Merchants & Categories"])


@router.get(
    "/v1/merchants",
    response_model=MerchantListResponse,
    summary="List merchants",
    description="""
    Get list of all cached merchants with transaction statistics.

    **Filters:**
    - Filter by category
    - Filter subscriptions only
    - Limit results

    **Returns:** Merchant name, category, transaction counts, total spent
    """,
)
async def get_merchants(
    category: Optional[str] = Query(None, description="Filter by category"),
    is_subscription: Optional[bool] = Query(
        None, description="Filter subscription merchants"
    ),
    limit: int = Query(50, ge=1, le=500, description="Results limit"),
):
    """Get list of merchants."""
    db = get_database()

    # Build filter
    filters = {}
    if category:
        filters["category"] = category
    if is_subscription is not None:
        filters["is_subscription"] = is_subscription

    # Get merchants
    merchants_cursor = db.merchants.find(filters).limit(limit)
    total_count = await db.merchants.count_documents(filters)

    merchants = []
    async for merchant in merchants_cursor:
        # Get transaction stats for this merchant
        txn_stats = await db.transactions_enriched.aggregate([
            {"$match": {"merchant.name": merchant["name"]}},
            {
                "$group": {
                    "_id": None,
                    "count": {"$sum": 1},
                    "total": {"$sum": "$amount"},
                }
            },
        ]).to_list(1)

        count = txn_stats[0]["count"] if txn_stats else 0
        total = txn_stats[0]["total"] if txn_stats else 0.0

        merchants.append(
            MerchantListItem(
                merchant_id=merchant["merchant_id"],
                name=merchant["name"],
                category=merchant.get("category"),
                subcategory=merchant.get("subcategory"),
                is_subscription=merchant.get("is_subscription", False),
                transaction_count=count,
                total_spent=total,
                aliases=merchant.get("aliases", []),
            )
        )

    return MerchantListResponse(
        merchants=merchants, total_count=total_count, limit=limit
    )


@router.get(
    "/v1/merchants/{merchant_id}",
    response_model=MerchantDetailResponse,
    summary="Get merchant details",
    description="""
    Get detailed information about a specific merchant.

    **Returns:**
    - Merchant metadata (name, category, tags)
    - Transaction statistics
    - Aliases (name variations found in CSVs)
    """,
)
async def get_merchant(merchant_id: str):
    """Get merchant details."""
    db = get_database()

    # Find merchant
    merchant = await db.merchants.find_one({"merchant_id": merchant_id})

    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant {merchant_id} not found",
        )

    # Get transaction statistics
    txn_stats = await db.transactions_enriched.aggregate([
        {"$match": {"merchant.name": merchant["name"]}},
        {
            "$group": {
                "_id": None,
                "count": {"$sum": 1},
                "total": {"$sum": "$amount"},
                "first_date": {"$min": "$date"},
                "last_date": {"$max": "$date"},
            }
        },
    ]).to_list(1)

    if txn_stats:
        stats = txn_stats[0]
        statistics = MerchantStats(
            transaction_count=stats["count"],
            total_spent=stats["total"],
            average_transaction=round(stats["total"] / stats["count"], 2),
            first_transaction=stats["first_date"].strftime("%Y-%m-%d"),
            last_transaction=stats["last_date"].strftime("%Y-%m-%d"),
        )
    else:
        statistics = MerchantStats(
            transaction_count=0,
            total_spent=0.0,
            average_transaction=0.0,
            first_transaction="N/A",
            last_transaction="N/A",
        )

    return MerchantDetailResponse(
        merchant_id=merchant["merchant_id"],
        name=merchant["name"],
        category=merchant.get("category"),
        subcategory=merchant.get("subcategory"),
        tags=merchant.get("tags", []),
        is_subscription=merchant.get("is_subscription", False),
        aliases=merchant.get("aliases", []),
        statistics=statistics,
    )


@router.get(
    "/v1/merchants/{merchant_id}/transactions",
    response_model=TransactionListResponse,
    summary="Get merchant transactions",
    description="""
    Get all transactions for a specific merchant.

    **Supports:**
    - Date range filtering
    - Pagination
    - Sorting
    """,
)
async def get_merchant_transactions(
    merchant_id: str,
    period: Optional[DatePeriod] = Query("current_month", description="Time period"),
    start_date: Optional[str] = Query(None, description="Custom start (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Custom end (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort: Literal["date", "amount"] = Query("date"),
    order: Literal["asc", "desc"] = Query("desc"),
):
    """Get transactions for a specific merchant."""
    db = get_database()

    # Find merchant to get name
    merchant = await db.merchants.find_one({"merchant_id": merchant_id})

    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant {merchant_id} not found",
        )

    # Get date range
    start_dt, end_dt = get_date_range(period, start_date, end_date)

    # Build filter
    filters = {
        "merchant.name": merchant["name"],
        "date": {"$gte": start_dt, "$lte": end_dt},
    }

    # Get total count
    total_count = await db.transactions_enriched.count_documents(filters)

    # Build sort
    sort_direction = -1 if order == "desc" else 1

    # Query transactions
    cursor = (
        db.transactions_enriched.find(filters)
        .sort(sort, sort_direction)
        .skip(offset)
        .limit(limit)
    )

    transactions = []
    async for txn in cursor:
        transactions.append(
            TransactionResponse(
                transaction_id=txn["transaction_id"],
                date=txn["date"],
                description=txn["description"],
                amount=txn["amount"],
                type=txn["type"],
                source_bank=txn["source_bank"],
                merchant=MerchantResponse(**txn["merchant"]),
                account=AccountResponse(**txn["account"]),
                tags=txn.get("tags", []),
                is_recurring=txn.get("is_recurring", False),
                category=txn["merchant"].get("category"),
            )
        )

    return TransactionListResponse(
        transactions=transactions,
        total_count=total_count,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total_count,
        filters_applied={"merchant_id": merchant_id, "period": format_period_name(period, start_date, end_date)},
    )


@router.get(
    "/v1/categories",
    response_model=CategoriesResponse,
    summary="List spending categories",
    description="""
    Get list of all spending categories with totals.

    **Returns:**
    - All categories ranked by spending
    - Transaction counts
    - Percentage of total spending
    - Average transaction amount

    **Use Case:** Budget planning, spending analysis
    """,
)
async def get_categories(
    period: Optional[DatePeriod] = Query("current_month", description="Time period"),
    start_date: Optional[str] = Query(None, description="Custom start (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Custom end (YYYY-MM-DD)"),
):
    """Get list of spending categories."""
    db = get_database()

    # Get date range
    start_dt, end_dt = get_date_range(period, start_date, end_date)

    # Build filter (debits only for spending categories)
    filters = {"date": {"$gte": start_dt, "$lte": end_dt}, "type": "debit"}

    # Get total expenses
    total_result = await db.transactions_enriched.aggregate([
        {"$match": filters},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]).to_list(1)
    total_expenses = total_result[0]["total"] if total_result else 0.0

    # Group by category
    pipeline = [
        {"$match": filters},
        {
            "$group": {
                "_id": "$merchant.category",
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"total": -1}},
    ]

    results = await db.transactions_enriched.aggregate(pipeline).to_list(None)

    categories = []
    for item in results:
        category_name = item["_id"] or "Uncategorized"
        total = item["total"]
        count = item["count"]
        percentage = (total / total_expenses * 100) if total_expenses > 0 else 0
        avg = total / count if count > 0 else 0

        categories.append(
            CategoryItem(
                category=category_name,
                total=total,
                count=count,
                percentage=round(percentage, 1),
                average_transaction=round(avg, 2),
            )
        )

    return CategoriesResponse(
        categories=categories,
        total_expenses=total_expenses,
        period=format_period_name(period, start_date, end_date),
    )
