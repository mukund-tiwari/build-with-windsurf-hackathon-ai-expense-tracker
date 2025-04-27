import pytest
from sqlmodel import create_engine, SQLModel

import app.database as database_module
import app.services.expense_service as exp_svc


@pytest.fixture(autouse=True)
def setup_db(monkeypatch, tmp_path):
    """
    Fixture to override the database engine to an in-memory SQLite DB before each test.
    """
    # Create in-memory SQLite engine
    # Use StaticPool to persist in-memory SQLite across connections
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Monkey-patch engines in both database_module and expense_service
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(exp_svc, "engine", engine)
    # Recreate tables
    SQLModel.metadata.create_all(engine)
    yield


def test_add_and_get_expense():
    # Add a single expense
    parsed = {"date": "2025-01-01", "amount": 10.5, "description": "Test item", "category": "food"}
    exp = exp_svc.add_expense(parsed, raw_nl="Test expense")
    assert exp.id == 1
    assert exp.amount == 10.5
    # Category should be normalized to title-case
    assert exp.category == "Food"

    # Retrieve all expenses
    all_expenses = exp_svc.get_expenses()
    assert len(all_expenses) == 1
    assert all_expenses[0].id == exp.id


def test_get_expenses_filters():
    # Add multiple expenses
    e1 = exp_svc.add_expense({"date": "2025-01-01", "amount": 5, "description": "A", "category": "cat1"}, "A")
    e2 = exp_svc.add_expense({"date": "2025-02-01", "amount": 15, "description": "B", "category": "cat2"}, "B")

    # Filter by category (title-case normalized)
    cat1 = exp_svc.get_expenses(category="Cat1")
    assert len(cat1) == 1 and cat1[0].id == e1.id



def test_summarize_expenses():
    # No expenses: total 0, empty breakdown
    summary = exp_svc.summarize_expenses()
    assert summary["total"] == 0
    assert summary["breakdown"] == []

    # Add expenses across two days
    exp_svc.add_expense({"date": "2025-01-01", "amount": 5, "description": "A", "category": None}, "A")
    exp_svc.add_expense({"date": "2025-01-02", "amount": 15, "description": "B", "category": None}, "B")

    # Total only
    summary_all = exp_svc.summarize_expenses()
    assert summary_all["total"] == 20

    # Daily breakdown (all entries logged at same timestamp)
    daily = exp_svc.summarize_expenses(granularity="daily")
    assert len(daily["breakdown"]) == 1

    # Monthly breakdown
    monthly = exp_svc.summarize_expenses(granularity="monthly")
    assert len(monthly["breakdown"]) == 1
    assert monthly["breakdown"][0]["total"] == 20