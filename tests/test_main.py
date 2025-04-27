import json
import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine

import app.database as database_module
import app.services.expense_service as exp_svc
import app.services.ai_service as ai_svc
import app.main as main_app

# Override the database engine for all tests
@pytest.fixture(autouse=True)
def setup_app_db(monkeypatch):
    # Create in-memory SQLite engine and patch modules
    # Use StaticPool for in-memory DB persistence across sessions
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(exp_svc, "engine", engine)
    # Initialize the database schema
    database_module.init_db()
    # Return a test client for the FastAPI app
    return TestClient(main_app.app)

def test_create_expense_endpoint(setup_app_db, monkeypatch):
    client = setup_app_db
    # Stub parse_expense to avoid real AI call
    parsed = {"date": "2025-01-05", "amount": 9.99, "description": "Test Desc", "category": "testcat"}
    monkeypatch.setattr(ai_svc, "parse_expense", lambda text: parsed)

    # Stub add_expense to return an object with dict() and timestamp
    dummy_data = {
        "id": 1,
        "timestamp": "2025-01-05T00:00:00",
        "amount": 9.99,
        "category": "testcat",
        "description": "Test Desc",
        "raw_nl": "Dummy input",
    }
    from datetime import datetime
    class DummyExpense:
        def __init__(self, data):
            self._data = data.copy()
            self.timestamp = datetime.fromisoformat(data["timestamp"])
        def dict(self):
            return self._data
    monkeypatch.setattr(exp_svc, "add_expense", lambda parsed, raw_nl: DummyExpense(dummy_data))
    response = client.post("/api/expenses", json={"text": "Dummy input"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["amount"] == 9.99
    assert data["category"] == "testcat"
    assert data["description"] == "Test Desc"
    assert data["raw_nl"] == "Dummy input"

def test_list_expenses_endpoint(setup_app_db, monkeypatch):
    client = setup_app_db
    # Stub get_expenses to return a list of dummy expenses
    dummy_list = [
        {"id": 1, "timestamp": "2025-02-01T00:00:00", "amount": 5, "category": "X", "description": "A", "raw_nl": "A"},
        {"id": 2, "timestamp": "2025-02-02T00:00:00", "amount": 10, "category": "Y", "description": "B", "raw_nl": "B"},
    ]
    monkeypatch.setattr(exp_svc, "get_expenses", lambda start_date=None, end_date=None, category=None: dummy_list)
    response = client.get("/api/expenses")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data == dummy_list

def test_ask_parse_expense_action(setup_app_db, monkeypatch):
    client = setup_app_db
    # Simulate AI function call for parse_expense
    message = {"function_call": {"name": "parse_expense", "arguments": json.dumps({"date": "2025-03-03", "amount": 7, "description": "C", "category": "cat"})}}
    monkeypatch.setattr(ai_svc, "call_openai", lambda text: message)
    # Stub add_expense to return object with dict() and timestamp attribute
    fake_data = {"id": 42, "timestamp": "2025-03-03T00:00:00", "amount": 7, "category": "cat", "description": "C", "raw_nl": "Add expense"}
    from datetime import datetime
    class DummyExp:
        def __init__(self, data):
            self._data = data.copy()
            self.timestamp = datetime.fromisoformat(data["timestamp"])
        def dict(self):
            return self._data
    monkeypatch.setattr(exp_svc, "add_expense", lambda args, nl: DummyExp(fake_data))
    response = client.post("/api/ask", json={"text": "Add expense"})
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "parse_expense"
    assert data["expense"]["id"] == 42

def test_ask_query_expenses_action(setup_app_db, monkeypatch):
    client = setup_app_db
    # Simulate AI function call for query_expenses
    args = {"start_date": "2025-01-01", "end_date": "2025-12-31", "category": "X"}
    message = {"function_call": {"name": "query_expenses", "arguments": json.dumps(args)}}
    monkeypatch.setattr(ai_svc, "call_openai", lambda text: message)
    # Stub get_expenses to return only matching items
    matching = [{"id": 10, "timestamp": "2025-06-06T00:00:00", "amount": 20, "category": "X", "description": "D", "raw_nl": "D"}]
    monkeypatch.setattr(exp_svc, "get_expenses", lambda start_date, end_date, category: matching)
    response = client.post("/api/ask", json={"text": "Query"})
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "query_expenses"
    assert data["expenses"] == matching

def test_ask_summarize_expenses_action(setup_app_db, monkeypatch):
    client = setup_app_db
    # Simulate AI function call for summarize_expenses
    args = {"start_date": "2025-01-01", "end_date": "2025-12-31", "granularity": "monthly"}
    message = {"function_call": {"name": "summarize_expenses", "arguments": json.dumps(args)}}
    monkeypatch.setattr(ai_svc, "call_openai", lambda text: message)
    # Stub summarize_expenses to return a fake summary
    fake_summary = {"total": 300, "breakdown": [{"period": "2025-01", "total": 100}, {"period": "2025-02", "total": 200}]}
    monkeypatch.setattr(exp_svc, "summarize_expenses", lambda start_date, end_date, granularity: fake_summary)
    response = client.post("/api/ask", json={"text": "Summary"})
    assert response.status_code == 200
    data = response.json()
    assert data["action"] == "summarize_expenses"
    assert data["summary"] == fake_summary
 
def test_ask_most_expensive_expense_action(setup_app_db, monkeypatch):
    client = setup_app_db
    # Seed the database with a few expenses
    exp_svc.add_expense({"amount": 100, "description": "A", "category": "cat"}, "A")
    exp_svc.add_expense({"amount": 200, "description": "B", "category": "cat"}, "B")
    exp_svc.add_expense({"amount": 150, "description": "C", "category": "cat"}, "C")
    # Simulate AI choosing get_most_expensive_expense
    message = {"function_call": {"name": "get_most_expensive_expense", "arguments": "{}"}}
    monkeypatch.setattr(ai_svc, "call_openai", lambda text: message)
    response = client.post("/api/ask", json={"text": "What was my most expensive expense ever?"})
    assert response.status_code == 200
    data = response.json()
    assert data.get("action") == "get_most_expensive_expense"
    exp = data.get("expense")
    assert exp["amount"] == 200
    assert exp["description"] == "B"

def test_ask_run_sql_second_highest_expense(setup_app_db, monkeypatch):
    client = setup_app_db
    # Seed the database
    exp_svc.add_expense({"amount": 50, "description": "X", "category": "cat"}, "X")
    exp_svc.add_expense({"amount": 200, "description": "Y", "category": "cat"}, "Y")
    exp_svc.add_expense({"amount": 150, "description": "Z", "category": "cat"}, "Z")
    # Simulate AI generating a run_sql call for second-most expensive
    sql = "SELECT amount, description FROM expense ORDER BY amount DESC LIMIT 1 OFFSET 1"
    message = {"function_call": {"name": "run_sql", "arguments": json.dumps({"sql": sql})}}
    monkeypatch.setattr(ai_svc, "call_openai", lambda text: message)
    response = client.post("/api/ask", json={"text": "What was my 2nd most expensive expense?"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("action") == "run_sql"
    # Ensure correct columns and single row returned
    assert data.get("columns") == ["amount", "description"]
    rows = data.get("rows")
    assert isinstance(rows, list) and len(rows) == 1
    row = rows[0]
    assert row["amount"] == 150
    assert row["description"] == "Z"