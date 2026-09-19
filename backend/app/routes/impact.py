"""Impact analytics routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.impact_service import get_impact_summary

router = APIRouter()

@router.get("")
def impact(organization_id: int = 1, db: Session = Depends(get_db)):
    return get_impact_summary(db, organization_id)
