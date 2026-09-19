"""Organization routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.organization import Organization
from app.models.department import Department
from app.models.resource import Resource

router = APIRouter()


@router.get("")
def list_organizations(db: Session = Depends(get_db)):
    result = []
    for org in db.query(Organization).all():
        total = db.query(Resource).filter(Resource.organization_id == org.id, Resource.status == "active").count()
        shareable = db.query(Resource).filter(Resource.organization_id == org.id, Resource.share_scope == "locality", Resource.status == "active").count()
        result.append({"id": org.id, "name": org.name, "code": org.code, "description": org.description,
                       "address": org.address, "share_scope": org.share_scope, "created_at": org.created_at,
                       "resource_count": total, "shareable_count": shareable})
    return result


@router.get("/{org_id}")
def get_organization(org_id: int, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org: raise HTTPException(status_code=404, detail="Organization not found")
    total = db.query(Resource).filter(Resource.organization_id == org.id, Resource.status == "active").count()
    return {"id": org.id, "name": org.name, "code": org.code, "description": org.description,
            "share_scope": org.share_scope, "resource_count": total}


@router.get("/{org_id}/departments")
def list_departments(org_id: int, db: Session = Depends(get_db)):
    result = []
    for d in db.query(Department).filter(Department.organization_id == org_id).all():
        count = db.query(Resource).filter(Resource.department_id == d.id, Resource.status == "active").count()
        result.append({"id": d.id, "name": d.name, "code": d.code, "description": d.description,
                       "head_name": d.head_name, "organization_id": d.organization_id, "resource_count": count})
    return result


@router.get("/network/overview")
def get_network_overview(db: Session = Depends(get_db)):
    nodes = []
    for org in db.query(Organization).all():
        total = db.query(Resource).filter(Resource.organization_id == org.id, Resource.status == "active").count()
        shareable = db.query(Resource).filter(Resource.organization_id == org.id, Resource.share_scope == "locality", Resource.status == "active").count()
        high_util = db.query(Resource).filter(Resource.organization_id == org.id, Resource.utilization > 80, Resource.status == "active").count()
        underutil = db.query(Resource).filter(Resource.organization_id == org.id, Resource.utilization < 30, Resource.availability.in_(["available", "underutilized"]), Resource.status == "active").count()
        nodes.append({"organization": {"id": org.id, "name": org.name, "code": org.code, "description": org.description},
                      "resources_total": total, "resources_shareable": shareable, "underutilized_count": underutil,
                      "potential_supply": underutil > 0, "potential_demand": high_util > 0})
    connections = []
    suppliers = [n for n in nodes if n["potential_supply"]]
    demanders = [n for n in nodes if n["potential_demand"]]
    for s in suppliers:
        for d in demanders:
            if s["organization"]["id"] != d["organization"]["id"]:
                connections.append({"from_organization": s["organization"]["name"], "to_organization": d["organization"]["name"],
                                    "available_resources": s["resources_shareable"], "type": "potential_match"})
    return {"nodes": nodes, "connections": connections, "total_organizations": len(nodes), "total_connections": len(connections)}
