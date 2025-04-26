from pydantic import BaseModel
from typing import Optional

class ExpenseCreate(BaseModel):
    """
    Request body for creating an expense from natural language.
    """
    text: str

class AskRequest(BaseModel):
    """
    Request body for asking the AI expense tracker queries.
    """
    text: str