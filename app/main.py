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