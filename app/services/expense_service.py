from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlmodel import Session, select
from sqlalchemy import func

from app.database import engine
from app.models import Expense


def add_expense(parsed: Dict[str, Any], raw_nl: str) -> Expense:
    """
    Persist a new expense from parsed data and original NL input.
    parsed should include: date (ISO str), amount (float), description (str), optional category (str).
    """
    # Parse timestamp from ISO date string; fallback to now
    try:
        ts = datetime.fromisoformat(parsed.get("date"))
    except Exception:
        ts = datetime.utcnow()

    expense = Expense(
        timestamp=ts,
        amount=float(parsed.get("amount", 0)),
        description=parsed.get("description"),
        category=parsed.get("category"),
        raw_nl=raw_nl,
    )
    with Session(engine) as session:
        session.add(expense)
        session.commit()
        session.refresh(expense)
    return expense


def get_expenses(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
) -> List[Expense]:
    """
    Retrieve expenses with optional filtering by date range and category.
    Dates should be ISO-format strings (YYYY-MM-DD).
    """
    stmt = select(Expense)
    # Apply date filters
    if start_date:
        try:
            dt = datetime.fromisoformat(start_date)
            stmt = stmt.where(Expense.timestamp >= dt)
        except ValueError:
            pass
    if end_date:
        try:
            # Include the full end date
            dt_end = datetime.fromisoformat(end_date) + timedelta(days=1)
            stmt = stmt.where(Expense.timestamp < dt_end)
        except ValueError:
            pass
    # Apply category filter
    if category:
        stmt = stmt.where(Expense.category == category)
    # Order by timestamp
    stmt = stmt.order_by(Expense.timestamp)
    with Session(engine) as session:
        results = session.exec(stmt).all()
    return results


def summarize_expenses(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Summarize expenses: total and optional breakdown by granularity (daily, weekly, monthly).
    """
    breakdown: List[Dict[str, Any]] = []
    # Build base filters
    filters = []
    if start_date:
        try:
            dt = datetime.fromisoformat(start_date)
            filters.append(Expense.timestamp >= dt)
        except ValueError:
            pass
    if end_date:
        try:
            dt_end = datetime.fromisoformat(end_date) + timedelta(days=1)
            filters.append(Expense.timestamp < dt_end)
        except ValueError:
            pass

    with Session(engine) as session:
        # Total sum
        total_stmt = select(func.coalesce(func.sum(Expense.amount), 0))
        if filters:
            total_stmt = total_stmt.where(*filters)
        total = session.exec(total_stmt).one()[0]

        # Breakdown
        if granularity in ("daily", "weekly", "monthly"):
            if granularity == "daily":
                fmt = "%Y-%m-%d"
            elif granularity == "weekly":
                fmt = "%Y-%W"
            else:
                fmt = "%Y-%m"
            period_field = func.strftime(fmt, Expense.timestamp)
            bd_stmt = (
                select(
                    period_field.label("period"),
                    func.sum(Expense.amount).label("total"),
                )
                .where(*filters)
                .group_by(period_field)
                .order_by(period_field)
            )
            rows = session.exec(bd_stmt).all()
            for period, amt in rows:
                breakdown.append({"period": period, "total": amt})

    return {"total": total, "breakdown": breakdown}