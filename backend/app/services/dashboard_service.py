"""Dashboard service."""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.resource import Resource
from app.models.department import Department
from app.models.impact import ImpactRecord


def get_dashboard(db: Session, organization_id: int = 1) -> Dict[str, Any]:
    base = db.query(Resource).filter(Resource.organization_id == organization_id, Resource.status == "active")
    total = base.count()
    available = base.filter(Resource.availability == "available").count()
    underutilized = base.filter(Resource.utilization < 50, Resource.availability.in_(["available", "underutilized", "in_use"])).count()
    in_maintenance = base.filter(Resource.availability == "maintenance").count()

    redistribution_opps = base.filter(Resource.utilization < 30, Resource.availability.in_(["available", "underutilized"])).count()
    repair_potential = base.filter(Resource.condition.in_(["fair", "poor"])).count()

    impact = db.query(
        func.coalesce(func.sum(ImpactRecord.resources_reused), 0),
        func.coalesce(func.sum(ImpactRecord.resources_repaired), 0),
        func.coalesce(func.sum(ImpactRecord.resources_redistributed), 0),
        func.coalesce(func.sum(ImpactRecord.resources_recycled), 0),
        func.coalesce(func.sum(ImpactRecord.purchases_avoided), 0),
        func.coalesce(func.sum(ImpactRecord.cost_avoided), 0),
        func.coalesce(func.sum(ImpactRecord.waste_avoided_kg), 0),
        func.coalesce(func.sum(ImpactRecord.co2_saved_kg), 0),
    ).filter(ImpactRecord.organization_id == organization_id).first()

    stats = {
        "total_resources": total, "available_resources": available,
        "underutilized_resources": underutilized, "in_maintenance": in_maintenance,
        "resources_matched": int(impact[0]), "resources_redistributed": int(impact[2]),
        "resources_repaired": int(impact[1]), "resources_recycled": int(impact[3]),
        "estimated_purchases_avoided": int(impact[4]),
        "estimated_cost_avoided": float(impact[5]), "estimated_waste_avoided_kg": float(impact[6]),
        "estimated_co2_saved_kg": float(impact[7]),
    }

    opportunities = [
        {"title": "Resources with unused potential", "description": f"{underutilized} resources could satisfy existing requirements", "count": underutilized, "icon": "trending_down"},
        {"title": "Redistribution opportunities", "description": f"{redistribution_opps} redistribution opportunities identified", "count": redistribution_opps, "icon": "swap_horiz"},
        {"title": "Repair potential", "description": f"{repair_potential} items have repair potential", "count": repair_potential, "icon": "build"},
    ]

    underutilized_list = []
    for r in base.filter(Resource.utilization < 50, Resource.availability.in_(["available", "underutilized", "in_use"])).order_by(Resource.utilization.asc()).limit(10).all():
        dept = db.query(Department).filter(Department.id == r.department_id).first()
        u = r.utilization or 0
        label = "high" if u < 20 else "medium" if u < 50 else "low"
        action = "Redistribute or reassign" if u < 20 else "Repair or recycle" if r.condition in ("poor", "non-functional") else "Redistribute to higher-need area"
        underutilized_list.append({"resource_id": r.resource_id, "name": r.name, "category": r.category, "type": r.type,
                                   "department": dept.name if dept else "Unknown", "utilization": u,
                                   "underutilization_score": label, "potential_action": action})

    category_dist = {row[0]: row[1] for row in db.query(Resource.category, func.count(Resource.id)).filter(Resource.organization_id == organization_id, Resource.status == "active").group_by(Resource.category).all()}
    condition_dist = {row[0]: row[1] for row in db.query(Resource.condition, func.count(Resource.id)).filter(Resource.organization_id == organization_id, Resource.status == "active").group_by(Resource.condition).all()}

    recent = db.query(Resource).filter(Resource.organization_id == organization_id).order_by(Resource.created_at.desc()).limit(5).all()
    recent_activity = [{"type": "resource_added", "description": f"Resource '{r.name}' added", "timestamp": r.created_at.isoformat() if r.created_at else None} for r in recent]

    return {"stats": stats, "opportunities": opportunities, "underutilized_resources": underutilized_list,
            "category_distribution": category_dist, "condition_distribution": condition_dist, "recent_activity": recent_activity}
