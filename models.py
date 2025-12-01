# models.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class Submission(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    message: Optional[str] = Field("", max_length=200)
    submitted_at: Optional[datetime] = None
