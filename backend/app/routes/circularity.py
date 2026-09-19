"""Circularity assessment routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.circularity import CircularityInput
from app.services.circularity_service import analyze_circularity

router = APIRouter()


@router.post("/analyze")
def analyze(input: CircularityInput, db: Session = Depends(get_db)):
    return analyze_circularity(db=db, description=input.description, image_url=input.image_url,
                               resource_id=input.resource_id, organization_id=input.organization_id)
