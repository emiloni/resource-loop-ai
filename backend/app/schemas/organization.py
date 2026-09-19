"""Pydantic schemas for organization."""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class OrganizationCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    address: Optional[str] = None
    share_scope: Optional[str] = "organization"


class OrganizationResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    address: Optional[str] = None
    share_scope: Optional[str] = "organization"
    created_at: Optional[datetime] = None
    resource_count: Optional[int] = 0
    shareable_count: Optional[int] = 0

    class Config:
        from_attributes = True


class DepartmentCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    head_name: Optional[str] = None
    organization_id: int


class DepartmentResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    head_name: Optional[str] = None
    organization_id: int
    created_at: Optional[datetime] = None
    resource_count: Optional[int] = 0

    class Config:
        from_attributes = True
