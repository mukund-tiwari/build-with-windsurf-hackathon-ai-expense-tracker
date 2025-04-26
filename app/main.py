import app.config  # Load environment variables from .env
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlmodel import SQLModel
import app.database as database_module
from datetime import datetime
from zoneinfo import ZoneInfo

# Helper to format timestamps in IST
def format_timestamp(dt: datetime) -> str:
    """Format a datetime to IST human-readable string."""
    try:
        ist = dt.astimezone(ZoneInfo("Asia/Kolkata"))
    except Exception:
        ist = dt
    # Include timezone abbreviation if available
    return ist.strftime("%Y-%m-%d %H:%M:%S %Z")

# Initialize FastAPI app
app = FastAPI(title="AI Expense Tracker")

# Create database tables on startup
@app.on_event("startup")
def on_startup():
    # Initialize the database schema using the (possibly monkey-patched) engine
    database_module.init_db()

from fastapi.middleware.cors import CORSMiddleware

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates directory
templates = Jinja2Templates(directory="templates")

@app.get("/health", response_model=dict)
def health():
    """
    Health check endpoint.
    """
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """
    Render the main UI page.
    """
    return templates.TemplateResponse("index.html", {"request": request})
 
# ---- API Endpoints ----
import json
from typing import List, Optional
from fastapi import Body, Query, HTTPException

import app.services.ai_service as ai_svc
import app.services.expense_service as exp_svc
from app.schemas import ExpenseCreate, AskRequest
from app.models import Expense as ExpenseModel

@app.post("/api/expenses")
def create_expense(expense_in: ExpenseCreate):
    """
    Create an expense from natural-language input.
    """
    # Parse with LLM
    try:
        parsed = ai_svc.parse_expense(expense_in.text)
        expense = exp_svc.add_expense(parsed, expense_in.text)
        # Prepare response with formatted timestamp and consistent category
        data = expense.dict() if hasattr(expense, "dict") else expense
        # Format timestamp
        data["timestamp"] = format_timestamp(expense.timestamp)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/expenses")
def list_expenses(
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    category:   Optional[str] = Query(None),
):
    """
    List stored expenses, optionally filtered by date range and/or category.
    """
    try:
        expenses = exp_svc.get_expenses(start_date, end_date, category)
        # Return list of dicts with formatted timestamps and consistent categories
        result = []
        for e in expenses:
            if hasattr(e, "dict"):
                d = e.dict()
                try:
                    d["timestamp"] = format_timestamp(e.timestamp)
                except Exception:
                    pass
            else:
                # assume dict with timestamp already formatted or raw
                d = e.copy()
            result.append(d)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/ask")
def ask(ask_req: AskRequest):
    """
    Handle free-form natural-language queries: parsing, querying, summarizing.
    """
    # Initial LLM call to decide on function
    message = ai_svc.call_openai(ask_req.text)
    func_call = message.get("function_call")
    # If no function call, return direct content
    if not func_call:
        return {"response": message.get("content")}
    name = func_call.get("name")
    args = json.loads(func_call.get("arguments") or "{}")
    # Route to appropriate service
    if name == "parse_expense":
        # Log new expense and respond with formatted timestamp & consistent category
        exp = exp_svc.add_expense(args, ask_req.text)
        expense_data = exp.dict() if hasattr(exp, "dict") else exp
        expense_data["timestamp"] = format_timestamp(exp.timestamp)
        return {"action": name, "expense": expense_data}
    if name == "query_expenses":
        # Return filtered expenses; format timestamps for model instances
        items = exp_svc.get_expenses(
            args.get("start_date"), args.get("end_date"), args.get("category")
        )
        expenses_data = []
        for e in items:
            if hasattr(e, "dict"):
                d = e.dict()
                try:
                    d["timestamp"] = format_timestamp(e.timestamp)
                except Exception:
                    pass
            else:
                # assume dict with timestamp already formatted or raw
                d = e.copy()
            expenses_data.append(d)
        return {"action": name, "expenses": expenses_data}
    if name == "summarize_expenses":
        summary = exp_svc.summarize_expenses(
            args.get("start_date"), args.get("end_date"), args.get("granularity")
        )
        return {"action": name, "summary": summary}
    if name == "get_last_expense":
        # If misclassified, parse as new expense; otherwise format last expense timestamp
        try:
            parsed = ai_svc.parse_expense(ask_req.text)
            exp = exp_svc.add_expense(parsed, ask_req.text)
            expense_data = exp.dict() if hasattr(exp, "dict") else exp
            expense_data["timestamp"] = format_timestamp(exp.timestamp)
            return {"action": "parse_expense", "expense": expense_data}
        except Exception:
            last = exp_svc.get_last_expense()
            # last["timestamp"] may be ISO; reformat to IST
            ts = last.get("timestamp")
            try:
                dt = datetime.fromisoformat(ts)
                last["timestamp"] = format_timestamp(dt)
            except Exception:
                pass
            return {"action": name, "expense": last}
    if name == "split_expense":
        split = exp_svc.split_expense(
            args.get("expense_id"), args.get("participant")
        )
        return {"action": name, "split": split}
    if name == "get_most_expensive_expense":
        # Retrieve and format the highest-expense record
        exp = exp_svc.get_most_expensive_expense()
        # Format timestamp in IST if present
        ts = exp.get("timestamp")
        try:
            dt = datetime.fromisoformat(ts)
            exp["timestamp"] = format_timestamp(dt)
        except Exception:
            pass
        return {"action": name, "expense": exp}
    if name == "run_sql":
        # Execute an arbitrary read-only SQL SELECT query
        sql = args.get("sql", "").strip()
        if not sql.lower().startswith("select"):  # Basic check
            raise HTTPException(status_code=400, detail="Only SELECT queries are allowed.")
        from sqlmodel import Session
        from sqlalchemy import text
        # Use the patched in-memory engine from database_module
        with Session(database_module.engine) as session:
            result_proxy = session.execute(text(sql))
            # Ensure columns are JSON-serializable
            cols = list(result_proxy.keys())
            rows = [dict(zip(cols, row)) for row in result_proxy.fetchall()]
        # Format any timestamp fields in the result
        for r in rows:
            if "timestamp" in r and isinstance(r["timestamp"], str):
                try:
                    dt = datetime.fromisoformat(r["timestamp"])
                    r["timestamp"] = format_timestamp(dt)
                except Exception:
                    pass
        return {"action": name, "columns": cols, "rows": rows}
    # Fallback to free-form response
    return {"response": message.get("content")}