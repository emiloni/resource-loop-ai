"""Pydantic schemas for documents."""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class DocumentResponse(BaseModel):
    id: int
    name: str
    filename: Optional[str]
    file_type: Optional[str]
    category: Optional[str]
    description: Optional[str]
    status: str
    chunk_count: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentQuery(BaseModel):
    query: str
    organization_id: int = 1


class DocumentQueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    disclaimer: str
