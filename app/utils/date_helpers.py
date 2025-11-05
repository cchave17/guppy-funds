"""Date range utilities for transaction queries."""

from datetime import datetime, timedelta
from typing import Tuple, Literal, Optional


DatePeriod = Literal["current_month", "last_30_days", "ytd", "all_time"]


def get_date_range(
    period: Optional[DatePeriod] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Tuple[datetime, datetime]:
    """
    Calculate date range based on period or custom dates.

    Args:
        period: Predefined period (current_month, last_30_days, ytd, all_time)
        start_date: Custom start date (YYYY-MM-DD)
        end_date: Custom end date (YYYY-MM-DD)

    Returns:
        Tuple of (start_datetime, end_datetime)
    """
    today = datetime.utcnow()

    # Custom date range takes precedence
    if start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59
        )
        return start, end

    # Use period
    period = period or "current_month"

    if period == "current_month":
        # First day of current month to now
        start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = today

    elif period == "last_30_days":
        # 30 days ago to now
        start = today - timedelta(days=30)
        end = today

    elif period == "ytd":
        # Year-to-date: January 1st to now
        start = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = today

    elif period == "all_time":
        # All transactions ever
        start = datetime(2000, 1, 1)
        end = today

    else:
        # Default to current month
        start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = today

    return start, end


def format_period_name(
    period: Optional[DatePeriod] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    """
    Get human-readable period name.

    Args:
        period: Period type
        start_date: Custom start
        end_date: Custom end

    Returns:
        Period name for display
    """
    if start_date and end_date:
        return f"custom ({start_date} to {end_date})"

    return period or "current_month"
