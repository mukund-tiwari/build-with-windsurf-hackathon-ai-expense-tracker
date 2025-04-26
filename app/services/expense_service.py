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
    # Use current time in IST as the timestamp for the expense
    try:
        # Python 3.9+ zoneinfo for IST
        from datetime import timezone
        from zoneinfo import ZoneInfo
        ts = datetime.now(tz=ZoneInfo("Asia/Kolkata"))
    except Exception:
        # Fallback to UTC now if zoneinfo unavailable
        ts = datetime.utcnow()

    # Normalize category for consistency (title-case)
    raw_cat = parsed.get("category")
    if raw_cat:
        cat = raw_cat.strip().title()
    else:
        cat = None
    expense = Expense(
        timestamp=ts,
        amount=float(parsed.get("amount", 0)),
        description=parsed.get("description"),
        category=cat,
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
        # Extract total as scalar
        try:
            total = session.exec(total_stmt).scalar_one()
        except AttributeError:
            # Fallback if scalar_one not available
            result = session.exec(total_stmt).one()
            total = result[0] if isinstance(result, (list, tuple)) else result

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

def get_last_expense() -> Dict[str, Any]:
    """
    Retrieve the most recently added expense.
    """
    with Session(engine) as session:
        stmt = select(Expense).order_by(Expense.timestamp.desc()).limit(1)
        result = session.exec(stmt).one_or_none()
    if not result:
        return {}
    exp = result
    return {
        "id": exp.id,
        "timestamp": exp.timestamp.isoformat(),
        "amount": exp.amount,
        "category": exp.category,
        "description": exp.description,
        "raw_nl": exp.raw_nl,
        "participants": exp.participants or []
    }

def split_expense(expense_id: int, participant: Optional[str] = None) -> Dict[str, Any]:
    """
    Compute the equal share for a given participant in an expense.
    If no participants are recorded, returns the full amount for 'me'.
    """
    with Session(engine) as session:
        stmt = select(Expense).where(Expense.id == expense_id)
        exp = session.exec(stmt).one_or_none()
    if not exp:
        raise ValueError(f"Expense with id {expense_id} not found.")
    parts = exp.participants or []
    # Default to self-only if no participants
    if not parts:
        parts = ["me"]
    count = len(parts)
    try:
        share = exp.amount / count
    except Exception:
        share = exp.amount
    who = participant or "me"
    return {
        "expense_id": expense_id,
        "participant": who,
        "share": share
    }
 
def get_most_expensive_expense() -> Dict[str, Any]:
    """
    Retrieve the expense record with the highest amount.
    """
    from sqlmodel import Session, select
    with Session(engine) as session:
        stmt = select(Expense).order_by(Expense.amount.desc()).limit(1)
        exp = session.exec(stmt).one_or_none()
    if not exp:
        return {}
    return {
        "id": exp.id,
        "timestamp": exp.timestamp.isoformat(),
        "amount": exp.amount,
        "category": exp.category,
        "description": exp.description,
        "raw_nl": exp.raw_nl,
        "participants": exp.participants or []
    }