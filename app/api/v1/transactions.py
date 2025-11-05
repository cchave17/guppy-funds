"""Transaction query endpoints."""

from typing import Optional, List, Literal
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException, status

from app.database import get_database
from app.api.v1.transaction_responses import (
    TransactionListResponse,
    TransactionResponse,
    TransactionDetailResponse,
    MerchantResponse,
    AccountResponse,
)
from app.api.v1.aggregation_responses import (
    TransactionSummaryResponse,
    ByCategoryResponse,
    ByMerchantResponse,
    ByMonthResponse,
    PeriodInfo,
    TotalsSummary,
    CategoryDetail,
    CategorySummaryItem,
    SubcategoryBreakdown,
    MerchantSummary,
    MonthSummary,
)
from app.utils.date_helpers import get_date_range, format_period_name, DatePeriod


router = APIRouter(
    prefix="/v1/transactions",
    tags=["Transactions"],
)


@router.get(
    "",
    response_model=TransactionListResponse,
    summary="Query transactions",
    description="""
    Query enriched transactions with flexible filtering and pagination.

    **Common Use Cases:**
    - All spending this month: `?type=debit`
    - Income this year: `?type=income&period=ytd`
    - Subscriptions: `?is_recurring=true`
    - Specific merchant: `?merchant=Amazon`
    - Custom date range: `?start_date=2025-10-01&end_date=2025-10-31`

    **Default Behavior:**
    - Returns current month transactions
    - Sorted by date (newest first)
    - Limit 50 per page
    """,
)
async def get_transactions(
    type: Optional[Literal["debit", "credit", "income"]] = Query(
        None, description="Filter by transaction type"
    ),
    category: Optional[str] = Query(None, description="Filter by merchant category"),
    source_bank: Optional[Literal["amex", "citi", "wells"]] = Query(
        None, description="Filter by bank source"
    ),
    merchant: Optional[str] = Query(
        None, description="Filter by merchant name (partial match)"
    ),
    is_recurring: Optional[bool] = Query(
        None, description="Filter recurring/subscription transactions"
    ),
    tags: Optional[str] = Query(
        None, description="Filter by tags (comma-separated)"
    ),
    period: Optional[DatePeriod] = Query(
        "current_month",
        description="Time period: current_month, last_30_days, ytd, or all_time",
    ),
    start_date: Optional[str] = Query(
        None, description="Custom start date (YYYY-MM-DD)"
    ),
    end_date: Optional[str] = Query(None, description="Custom end date (YYYY-MM-DD)"),
    min_amount: Optional[float] = Query(None, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, description="Maximum amount"),
    limit: int = Query(50, ge=1, le=500, description="Results per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    sort: Literal["date", "amount"] = Query("date", description="Sort field"),
    order: Literal["asc", "desc"] = Query("desc", description="Sort order"),
):
    """Query transactions with filtering, sorting, and pagination."""
    db = get_database()

    # Build MongoDB filter
    filters = {}

    # Transaction type filter
    if type:
        filters["type"] = type

    # Category filter
    if category:
        filters["merchant.category"] = category

    # Source bank filter
    if source_bank:
        filters["source_bank"] = source_bank

    # Merchant filter (partial match, case-insensitive)
    if merchant:
        filters["merchant.name"] = {"$regex": merchant, "$options": "i"}

    # Recurring filter
    if is_recurring is not None:
        filters["is_recurring"] = is_recurring

    # Tags filter
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        filters["tags"] = {"$in": tag_list}

    # Amount range filters
    if min_amount is not None:
        filters["amount"] = filters.get("amount", {})
        filters["amount"]["$gte"] = min_amount

    if max_amount is not None:
        filters["amount"] = filters.get("amount", {})
        filters["amount"]["$lte"] = max_amount

    # Date range filter
    start_dt, end_dt = get_date_range(period, start_date, end_date)
    filters["date"] = {"$gte": start_dt, "$lte": end_dt}

    # Get total count (for pagination)
    total_count = await db.transactions_enriched.count_documents(filters)

    # Build sort
    sort_field = sort
    sort_direction = -1 if order == "desc" else 1

    # Query transactions
    cursor = (
        db.transactions_enriched.find(filters)
        .sort(sort_field, sort_direction)
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

    # Build filters applied summary
    filters_applied = {}
    if type:
        filters_applied["type"] = type
    if category:
        filters_applied["category"] = category
    if source_bank:
        filters_applied["source_bank"] = source_bank
    if merchant:
        filters_applied["merchant"] = merchant
    if is_recurring is not None:
        filters_applied["is_recurring"] = is_recurring
    filters_applied["period"] = format_period_name(period, start_date, end_date)

    return TransactionListResponse(
        transactions=transactions,
        total_count=total_count,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total_count,
        filters_applied=filters_applied,
    )


@router.get(
    "/income",
    response_model=TransactionListResponse,
    summary="Get income transactions",
    description="""
    Convenient shortcut for querying income transactions.

    Equivalent to: `GET /v1/transactions?type=income`

    Returns all payroll, direct deposits, and salary transactions.
    Defaults to current month.
    """,
)
async def get_income(
    period: Optional[DatePeriod] = Query(
        "current_month", description="Time period filter"
    ),
    start_date: Optional[str] = Query(None, description="Custom start (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Custom end (YYYY-MM-DD)"),
    source_bank: Optional[Literal["amex", "citi", "wells"]] = Query(
        None, description="Filter by bank"
    ),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort: Literal["date", "amount"] = Query("date"),
    order: Literal["asc", "desc"] = Query("desc"),
):
    """Get all income transactions."""
    return await get_transactions(
        type="income",
        category=None,
        source_bank=source_bank,
        merchant=None,
        is_recurring=None,
        tags=None,
        period=period,
        start_date=start_date,
        end_date=end_date,
        min_amount=None,
        max_amount=None,
        limit=limit,
        offset=offset,
        sort=sort,
        order=order,
    )


@router.get(
    "/expenses",
    response_model=TransactionListResponse,
    summary="Get expense transactions",
    description="""
    Convenient shortcut for querying expense (debit) transactions.

    Equivalent to: `GET /v1/transactions?type=debit`

    Returns all spending: groceries, restaurants, shopping, bills, etc.
    Excludes income and credits.
    Defaults to current month.
    """,
)
async def get_expenses(
    category: Optional[str] = Query(None, description="Filter by category"),
    source_bank: Optional[Literal["amex", "citi", "wells"]] = Query(
        None, description="Filter by bank"
    ),
    merchant: Optional[str] = Query(None, description="Filter by merchant name"),
    period: Optional[DatePeriod] = Query(
        "current_month", description="Time period filter"
    ),
    start_date: Optional[str] = Query(None, description="Custom start (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Custom end (YYYY-MM-DD)"),
    min_amount: Optional[float] = Query(None, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, description="Maximum amount"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort: Literal["date", "amount"] = Query("date"),
    order: Literal["asc", "desc"] = Query("desc"),
):
    """Get all expense (debit) transactions."""
    return await get_transactions(
        type="debit",
        category=category,
        source_bank=source_bank,
        merchant=merchant,
        is_recurring=None,
        tags=None,
        period=period,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        limit=limit,
        offset=offset,
        sort=sort,
        order=order,
    )


@router.get(
    "/subscriptions",
    response_model=TransactionListResponse,
    summary="Get subscription/recurring transactions",
    description="""
    Convenient shortcut for querying recurring subscription transactions.

    Equivalent to: `GET /v1/transactions?is_recurring=true`

    Returns recurring payments like:
    - Subscription services (Netflix, Spotify, etc.)
    - Recurring bills (utilities, internet, etc.)
    - Payroll (income marked as recurring)

    Defaults to current month.
    """,
)
async def get_subscriptions(
    type: Optional[Literal["debit", "credit", "income"]] = Query(
        None, description="Filter by transaction type"
    ),
    category: Optional[str] = Query(None, description="Filter by category"),
    source_bank: Optional[Literal["amex", "citi", "wells"]] = Query(
        None, description="Filter by bank"
    ),
    period: Optional[DatePeriod] = Query(
        "current_month", description="Time period filter"
    ),
    start_date: Optional[str] = Query(None, description="Custom start (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Custom end (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort: Literal["date", "amount"] = Query("date"),
    order: Literal["asc", "desc"] = Query("desc"),
):
    """Get all recurring/subscription transactions."""
    return await get_transactions(
        type=type,
        category=category,
        source_bank=source_bank,
        merchant=None,
        is_recurring=True,
        tags=None,
        period=period,
        start_date=start_date,
        end_date=end_date,
        min_amount=None,
        max_amount=None,
        limit=limit,
        offset=offset,
        sort=sort,
        order=order,
    )


@router.get(
    "/summary",
    response_model=TransactionSummaryResponse,
    summary="Get financial summary",
    description="""
    High-level financial overview with income, expenses, and bank breakdowns.

    **Returns:**
    - Total income and expenses
    - Net cash flow
    - Per-bank breakdown (checking vs credit cards)
    - Top spending categories

    **Perfect for:** Dashboard overview, monthly review
    """,
)
async def get_summary(
    period: Optional[DatePeriod] = Query("current_month", description="Time period"),
    start_date: Optional[str] = Query(None, description="Custom start (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Custom end (YYYY-MM-DD)"),
):
    """Get financial summary with totals and breakdowns."""
    db = get_database()

    # Get date range
    start_dt, end_dt = get_date_range(period, start_date, end_date)
    date_filter = {"date": {"$gte": start_dt, "$lte": end_dt}}

    # Calculate totals
    income_pipeline = [
        {"$match": {**date_filter, "type": "income"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
    ]
    income_result = await db.transactions_enriched.aggregate(income_pipeline).to_list(1)
    total_income = income_result[0]["total"] if income_result else 0.0
    income_count = income_result[0]["count"] if income_result else 0

    expenses_pipeline = [
        {"$match": {**date_filter, "type": "debit"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
    ]
    expenses_result = await db.transactions_enriched.aggregate(expenses_pipeline).to_list(1)
    total_expenses = expenses_result[0]["total"] if expenses_result else 0.0
    expenses_count = expenses_result[0]["count"] if expenses_result else 0

    # By-bank breakdown
    by_bank = {}
    for bank in ["wells", "amex", "citi"]:
        bank_filter = {**date_filter, "source_bank": bank}

        if bank == "wells":
            # Checking account: income - expenses
            income = await db.transactions_enriched.aggregate([
                {"$match": {**bank_filter, "type": "income"}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
            ]).to_list(1)
            expenses = await db.transactions_enriched.aggregate([
                {"$match": {**bank_filter, "type": "debit"}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
            ]).to_list(1)

            bank_income = income[0]["total"] if income else 0.0
            bank_expenses = expenses[0]["total"] if expenses else 0.0

            by_bank[bank] = {
                "income": bank_income,
                "expenses": bank_expenses,
                "net": bank_income - bank_expenses,
                "running_balance": bank_income - bank_expenses,
            }
        else:
            # Credit cards: debits - payments
            charges = await db.transactions_enriched.aggregate([
                {"$match": {**bank_filter, "type": "debit"}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
            ]).to_list(1)
            payments = await db.transactions_enriched.aggregate([
                {"$match": {**bank_filter, "type": "credit"}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
            ]).to_list(1)

            bank_charges = charges[0]["total"] if charges else 0.0
            bank_payments = payments[0]["total"] if payments else 0.0

            by_bank[bank] = {
                "expenses": bank_charges,
                "payments": bank_payments,
                "amount_owed": -(bank_charges - bank_payments),  # Negative = debt
            }

    # Top categories
    category_pipeline = [
        {"$match": {**date_filter, "type": "debit"}},
        {
            "$group": {
                "_id": "$merchant.category",
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"total": -1}},
        {"$limit": 5},
    ]
    category_results = await db.transactions_enriched.aggregate(category_pipeline).to_list(5)

    top_categories = [
        CategorySummaryItem(
            category=cat["_id"] or "Uncategorized",
            total=cat["total"],
            count=cat["count"],
        )
        for cat in category_results
    ]

    return TransactionSummaryResponse(
        period=PeriodInfo(
            start=start_dt.strftime("%Y-%m-%d"),
            end=end_dt.strftime("%Y-%m-%d"),
            type=format_period_name(period, start_date, end_date),
        ),
        totals=TotalsSummary(
            income=total_income,
            expenses=total_expenses,
            net=total_income - total_expenses,
            transaction_count=income_count + expenses_count,
        ),
        by_bank=by_bank,
        top_categories=top_categories,
    )


@router.get(
    "/by-category",
    response_model=ByCategoryResponse,
    summary="Spending by category",
    description="""
    Break down spending by category with stats.

    **Returns:**
    - All categories with totals and transaction counts
    - Percentage of total spending
    - Average transaction amount
    - Subcategory breakdowns

    **Use Case:** Budget analysis, "Where is my money going?"
    """,
)
async def get_by_category(
    period: Optional[DatePeriod] = Query("current_month", description="Time period"),
    start_date: Optional[str] = Query(None, description="Custom start (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Custom end (YYYY-MM-DD)"),
    source_bank: Optional[Literal["amex", "citi", "wells"]] = Query(
        None, description="Filter by bank"
    ),
):
    """Get spending breakdown by category."""
    db = get_database()

    # Get date range
    start_dt, end_dt = get_date_range(period, start_date, end_date)

    # Build filter
    filters = {"date": {"$gte": start_dt, "$lte": end_dt}, "type": "debit"}
    if source_bank:
        filters["source_bank"] = source_bank

    # Total expenses
    total_result = await db.transactions_enriched.aggregate([
        {"$match": filters},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]).to_list(1)
    total_expenses = total_result[0]["total"] if total_result else 0.0

    # Group by category
    category_pipeline = [
        {"$match": filters},
        {
            "$group": {
                "_id": {
                    "category": "$merchant.category",
                    "subcategory": "$merchant.subcategory",
                },
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"total": -1}},
    ]

    results = await db.transactions_enriched.aggregate(category_pipeline).to_list(None)

    # Group by category with subcategories
    categories_map = {}
    for item in results:
        category = item["_id"]["category"] or "Uncategorized"
        subcategory = item["_id"]["subcategory"]

        if category not in categories_map:
            categories_map[category] = {
                "total": 0.0,
                "count": 0,
                "subcategories": [],
            }

        categories_map[category]["total"] += item["total"]
        categories_map[category]["count"] += item["count"]

        if subcategory:
            categories_map[category]["subcategories"].append(
                SubcategoryBreakdown(
                    name=subcategory, total=item["total"], count=item["count"]
                )
            )

    # Build response
    categories = []
    for cat_name, cat_data in sorted(
        categories_map.items(), key=lambda x: x[1]["total"], reverse=True
    ):
        percentage = (
            (cat_data["total"] / total_expenses * 100) if total_expenses > 0 else 0
        )
        avg = cat_data["total"] / cat_data["count"] if cat_data["count"] > 0 else 0

        categories.append(
            CategoryDetail(
                category=cat_name,
                total=cat_data["total"],
                count=cat_data["count"],
                percentage=round(percentage, 1),
                average_transaction=round(avg, 2),
                subcategories=cat_data["subcategories"],
            )
        )

    return ByCategoryResponse(
        period=format_period_name(period, start_date, end_date),
        total_expenses=total_expenses,
        categories=categories,
    )


@router.get(
    "/by-merchant",
    response_model=ByMerchantResponse,
    summary="Spending by merchant",
    description="""
    Top merchants by total spending.

    **Returns:**
    - Merchants ranked by total spent (highest first)
    - Transaction counts and averages
    - First and last transaction dates
    - Subscription status

    **Use Case:** "Who am I spending the most with?"
    """,
)
async def get_by_merchant(
    period: Optional[DatePeriod] = Query("current_month", description="Time period"),
    start_date: Optional[str] = Query(None, description="Custom start (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Custom end (YYYY-MM-DD)"),
    limit: int = Query(20, ge=1, le=100, description="Number of top merchants"),
):
    """Get spending breakdown by merchant."""
    db = get_database()

    # Get date range
    start_dt, end_dt = get_date_range(period, start_date, end_date)

    # Aggregate by merchant (debits only)
    pipeline = [
        {"$match": {"date": {"$gte": start_dt, "$lte": end_dt}, "type": "debit"}},
        {
            "$group": {
                "_id": "$merchant.name",
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1},
                "category": {"$first": "$merchant.category"},
                "first_date": {"$min": "$date"},
                "last_date": {"$max": "$date"},
                "is_recurring": {"$first": "$is_recurring"},
            }
        },
        {"$sort": {"total": -1}},
        {"$limit": limit},
    ]

    results = await db.transactions_enriched.aggregate(pipeline).to_list(limit)

    # Get merchant IDs from merchants collection
    merchants = []
    for item in results:
        merchant_name = item["_id"]

        # Look up merchant_id
        merchant_doc = await db.merchants.find_one({"name": merchant_name})
        merchant_id = merchant_doc["merchant_id"] if merchant_doc else merchant_name.lower().replace(" ", "-")

        merchants.append(
            MerchantSummary(
                merchant_id=merchant_id,
                merchant_name=merchant_name,
                category=item.get("category"),
                is_subscription=item.get("is_recurring", False),
                total_spent=item["total"],
                transaction_count=item["count"],
                average_transaction=round(item["total"] / item["count"], 2),
                first_transaction=item["first_date"].strftime("%Y-%m-%d"),
                last_transaction=item["last_date"].strftime("%Y-%m-%d"),
            )
        )

    total_count = await db.merchants.count_documents({})

    return ByMerchantResponse(
        period=format_period_name(period, start_date, end_date),
        total_count=total_count,
        merchants=merchants,
        limit=limit,
    )


@router.get(
    "/by-month",
    response_model=ByMonthResponse,
    summary="Monthly spending trends",
    description="""
    Monthly breakdown of income, expenses, and net cash flow.

    **Returns:**
    - Month-by-month summary (last 12 months by default)
    - Income vs expenses per month
    - Net cash flow
    - Top category for each month

    **Use Case:** Trend analysis, "Am I saving more this month?"
    """,
)
async def get_by_month(
    period: Optional[DatePeriod] = Query("ytd", description="Time period (default: ytd)"),
    start_date: Optional[str] = Query(None, description="Custom start (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Custom end (YYYY-MM-DD)"),
):
    """Get monthly breakdown of transactions."""
    db = get_database()

    # Get date range
    start_dt, end_dt = get_date_range(period, start_date, end_date)

    # Aggregate by month
    pipeline = [
        {"$match": {"date": {"$gte": start_dt, "$lte": end_dt}}},
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$date"},
                    "month": {"$month": "$date"},
                },
                "income": {
                    "$sum": {"$cond": [{"$eq": ["$type", "income"]}, "$amount", 0]}
                },
                "expenses": {
                    "$sum": {"$cond": [{"$eq": ["$type", "debit"]}, "$amount", 0]}
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id.year": -1, "_id.month": -1}},
    ]

    results = await db.transactions_enriched.aggregate(pipeline).to_list(None)

    months = []
    for item in results:
        year = item["_id"]["year"]
        month = item["_id"]["month"]
        income = item["income"]
        expenses = item["expenses"]

        # Get top category for this month (optional - can be slow)
        # For now, just omit it to keep things fast

        months.append(
            MonthSummary(
                month=f"{year}-{month:02d}",
                year=year,
                income=income,
                expenses=expenses,
                net=income - expenses,
                transaction_count=item["count"],
                top_category=None,  # Can add later if needed
            )
        )

    return ByMonthResponse(
        range=format_period_name(period, start_date, end_date), months=months
    )


# IMPORTANT: Path parameter route MUST come last to avoid matching specific paths
@router.get(
    "/{transaction_id}",
    response_model=TransactionDetailResponse,
    summary="Get transaction by ID",
    description="Retrieve detailed information for a specific transaction.",
)
async def get_transaction_by_id(transaction_id: str):
    """Get a single transaction by ID."""
    db = get_database()

    transaction = await db.transactions_enriched.find_one(
        {"transaction_id": transaction_id}
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found",
        )

    # Remove MongoDB _id for response
    transaction.pop("_id", None)

    return TransactionDetailResponse(**transaction)
