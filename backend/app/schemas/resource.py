"""Pydantic schemas for Resource."""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class ResourceCreate(BaseModel):
    resource_id: str
    category: str
    type: str
    name: str
    description: Optional[str] = None
    condition: Optional[str] = "Good"
    availability: Optional[str] = "available"
    utilization: Optional[int] = 0
    location: Optional[str] = None
    building: Optional[str] = None
    room: Optional[str] = None
    organization_id: int
    department_id: int
    purchase_date: Optional[datetime] = None
    remaining_useful_life_months: Optional[int] = 36
    specifications: Optional[Dict[str, Any]] = {}
    share_scope: Optional[str] = "organization"
    original_cost: Optional[float] = None
    estimated_current_value: Optional[float] = None
    image_url: Optional[str] = None


class ResourceUpdate(BaseModel):
    category: Optional[str] = None
    type: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    condition: Optional[str] = None
    availability: Optional[str] = None
    utilization: Optional[int] = None
    location: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    share_scope: Optional[str] = None


class ResourceResponse(BaseModel):
    id: int
    resource_id: str
    organization_id: int
    department_id: int
    category: str
    type: str
    name: str
    description: Optional[str] = None
    condition: Optional[str] = None
    availability: Optional[str] = None
    utilization: Optional[int] = 0
    status: str = "active"
    location: Optional[str] = None
    building: Optional[str] = None
    room: Optional[str] = None
    purchase_date: Optional[datetime] = None
    remaining_useful_life_months: Optional[int] = None
    specifications: Optional[Dict[str, Any]] = {}
    share_scope: Optional[str] = "organization"
    original_cost: Optional[float] = None
    estimated_current_value: Optional[float] = None
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    organization_name: Optional[str] = None
    department_name: Optional[str] = None

    class Config:
        from_attributes = True


class ResourceListResponse(BaseModel):
    resources: List[ResourceResponse]
    total: int
    page: int
    per_page: int
    pages: int


class ImportPreview(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: List[Dict[str, Any]]
    preview_data: List[Dict[str, Any]]
