"""Resource CRUD routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database.connection import get_db
from app.models.resource import Resource
from app.models.department import Department
from app.models.organization import Organization

router = APIRouter()


def _enrich(r, db):
    org = db.query(Organization).filter(Organization.id == r.organization_id).first()
    dept = db.query(Department).filter(Department.id == r.department_id).first()
    return {"id": r.id, "resource_id": r.resource_id, "organization_id": r.organization_id, "department_id": r.department_id,
            "category": r.category, "type": r.type, "name": r.name, "description": r.description,
            "condition": r.condition, "availability": r.availability, "utilization": r.utilization, "status": r.status,
            "location": r.location, "building": r.building, "room": r.room,
            "purchase_date": r.purchase_date, "remaining_useful_life_months": r.remaining_useful_life_months,
            "specifications": r.specifications or {}, "share_scope": r.share_scope,
            "original_cost": r.original_cost, "estimated_current_value": r.estimated_current_value,
            "image_url": r.image_url, "created_at": r.created_at, "updated_at": r.updated_at,
            "organization_name": org.name if org else None, "department_name": dept.name if dept else None}


@router.get("")
def list_resources(category: Optional[str] = None, type: Optional[str] = None, condition: Optional[str] = None,
                   availability: Optional[str] = None, organization_id: Optional[int] = None,
                   department_id: Optional[int] = None, search: Optional[str] = None,
                   page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
                   db: Session = Depends(get_db)):
    q = db.query(Resource).filter(Resource.status == "active")
    if category: q = q.filter(Resource.category == category)
    if type: q = q.filter(Resource.type == type)
    if condition: q = q.filter(Resource.condition == condition)
    if availability: q = q.filter(Resource.availability == availability)
    if organization_id: q = q.filter(Resource.organization_id == organization_id)
    if department_id: q = q.filter(Resource.department_id == department_id)
    if search:
        t = f"%{search}%"
        q = q.filter(Resource.name.ilike(t) | Resource.description.ilike(t) | Resource.resource_id.ilike(t) | Resource.type.ilike(t))
    total = q.count()
    pages = (total + per_page - 1) // per_page
    resources = q.offset((page - 1) * per_page).limit(per_page).all()
    return {"resources": [_enrich(r, db) for r in resources], "total": total, "page": page, "per_page": per_page, "pages": pages}


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    return [r[0] for r in db.query(Resource.category).distinct().filter(Resource.status == "active").all()]


@router.get("/stats")
def get_stats(organization_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(Resource).filter(Resource.status == "active")
    if organization_id: q = q.filter(Resource.organization_id == organization_id)
    return {"total": q.count(), "available": q.filter(Resource.availability == "available").count(),
            "in_use": q.filter(Resource.availability == "in_use").count(),
            "underutilized": q.filter(Resource.availability == "underutilized").count(),
            "maintenance": q.filter(Resource.availability == "maintenance").count()}


@router.get("/{resource_id}")
def get_resource(resource_id: int, db: Session = Depends(get_db)):
    r = db.query(Resource).filter(Resource.id == resource_id).first()
    if not r: raise HTTPException(status_code=404, detail="Resource not found")
    return _enrich(r, db)


@router.post("", status_code=201)
def create_resource(resource: dict, db: Session = Depends(get_db)):
    if db.query(Resource).filter(Resource.resource_id == resource.get("resource_id"), Resource.organization_id == resource.get("organization_id")).first():
        raise HTTPException(status_code=400, detail="Resource ID already exists")
    db_r = Resource(**resource)
    db.add(db_r); db.commit(); db.refresh(db_r)
    return _enrich(db_r, db)


@router.put("/{resource_id}")
def update_resource(resource_id: int, update: dict, db: Session = Depends(get_db)):
    r = db.query(Resource).filter(Resource.id == resource_id).first()
    if not r: raise HTTPException(status_code=404, detail="Resource not found")
    for k, v in update.items():
        if v is not None: setattr(r, k, v)
    db.commit(); db.refresh(r)
    return _enrich(r, db)


@router.delete("/{resource_id}")
def delete_resource(resource_id: int, db: Session = Depends(get_db)):
    r = db.query(Resource).filter(Resource.id == resource_id).first()
    if not r: raise HTTPException(status_code=404, detail="Resource not found")
    r.status = "inactive"; db.commit()
    return {"message": "Resource deleted", "id": resource_id}
