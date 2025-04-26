import app.config  # Load environment variables from .env
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlmodel import SQLModel

from app.database import engine, init_db

# Initialize FastAPI app
app = FastAPI(title="AI Expense Tracker")

# Create database tables on startup
@app.on_event("startup")
def on_startup():
    init_db()

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

@app.post("/api/expenses", response_model=ExpenseModel)
def create_expense(expense_in: ExpenseCreate):
    """
    Create an expense from natural-language input.
    """
    # Parse with LLM
    try:
        parsed = ai_svc.parse_expense(expense_in.text)
        expense = exp_svc.add_expense(parsed, expense_in.text)
        return expense
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/expenses", response_model=List[ExpenseModel])
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
        return expenses
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
        exp = exp_svc.add_expense(args, ask_req.text)
        return {"action": name, "expense": exp.dict()}
    if name == "query_expenses":
        items = exp_svc.get_expenses(
            args.get("start_date"), args.get("end_date"), args.get("category")
        )
        return {"action": name, "expenses": [e.dict() for e in items]}
    if name == "summarize_expenses":
        summary = exp_svc.summarize_expenses(
            args.get("start_date"), args.get("end_date"), args.get("granularity")
        )
        return {"action": name, "summary": summary}
    # Fallback
    return {"response": message.get("content")}