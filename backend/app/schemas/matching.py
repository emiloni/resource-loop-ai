"""Pydantic schemas for matching."""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class RequirementInput(BaseModel):
    raw_query: str
    organization_id: Optional[int] = 1
    department_id: Optional[int] = None


class MatchingResponse(BaseModel):
    parsed_requirements: Dict[str, Any]
    total_compatible: int
    recommended_combination: Optional[Dict[str, Any]]
    individual_matches: List[Dict[str, Any]]
    message: str
