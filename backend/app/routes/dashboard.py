"""Dashboard routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.dashboard_service import get_dashboard

router = APIRouter()

@router.get("")
def dashboard(organization_id: int = 1, db: Session = Depends(get_db)):
    return get_dashboard(db, organization_id)
