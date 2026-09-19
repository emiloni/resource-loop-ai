"""Pydantic schemas for circularity."""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class CircularityInput(BaseModel):
    description: Optional[str] = None
    image_url: Optional[str] = None
    resource_id: Optional[int] = None
    organization_id: int = 1


class CircularityResponse(BaseModel):
    id: Optional[int] = None
    detected_object: Optional[str] = None
    detected_material: Optional[str] = None
    detected_condition: Optional[str] = None
    detected_damage: Optional[str] = None
    repairability: Optional[str] = None
    estimated_remaining_life_months: Optional[int] = None
    recommendations: List[Dict[str, Any]]
    recommended_action: str
    recommended_explanation: str
    confidence: float
    created_at: Optional[datetime] = None
