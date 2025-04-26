from typing import Optional, List
from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.types import JSON

class Expense(SQLModel, table=True):
    """
    Expense model representing a single expense record.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    amount: float = Field(nullable=False)
    category: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    raw_nl: str = Field(nullable=False, description="Original natural-language input")
    participants: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description="List of participants for group expenses"
    )