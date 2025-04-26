from typing import Optional
from datetime import datetime

from sqlmodel import SQLModel, Field

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