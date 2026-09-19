"""Resource request routes — full transfer-request workflow."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from typing import Optional
import json as _json

from app.database.connection import get_db
from app.models.resource_request import ResourceRequest, ContactMessage
from app.models.resource import Resource
from app.models.user import User
from app.models.department import Department
from app.models.organization import Organization

router = APIRouter()


def _gen_request_id(db: Session) -> str:
    """Generate a unique request ID like REQ-2026-00124."""
    year = datetime.utcnow().year
    count = db.query(ResourceRequest).count() + 1
    return f"REQ-{year}-{count:05d}"


def _enrich_request(r, db):
    """Add related names to a request."""
    resource = db.query(Resource).filter(Resource.id == r.resource_id).first()
    requester = db.query(User).filter(User.id == r.requester_id).first() if r.requester_id else None
    req_org = db.query(Organization).filter(Organization.id == r.requester_organization_id).first()
    req_dept = db.query(Department).filter(Department.id == r.requester_department_id).first()

    # Resource's current owner/department
    res_dept = db.query(Department).filter(Department.id == resource.department_id).first() if resource else None
    res_org = db.query(Organization).filter(Organization.id == resource.organization_id).first() if resource else None
    owner = db.query(User).filter(User.id == resource.owner_id).first() if resource and resource.owner_id else None

    return {
        "id": r.id,
        "request_id": r.request_id,
        "resource_id": r.resource_id,
        "resource_name": resource.name if resource else "Unknown",
        "resource_code": resource.resource_id if resource else "",
        "resource_condition": resource.condition if resource else "",
        "resource_utilization": resource.utilization if resource else 0,
        "resource_location": resource.location if resource else "",
        "resource_availability": resource.availability if resource else "",
        "resource_department_name": res_dept.name if res_dept else "",
        "resource_organization_name": res_org.name if res_org else "",
        "owner_name": owner.full_name if owner else (res_dept.head_name if res_dept else "Department Admin"),
        "owner_email": owner.email if owner else "",
        "owner_department_name": res_dept.name if res_dept else "",
        "requester_name": requester.full_name if requester else "Unknown",
        "requester_username": requester.username if requester else "",
        "requester_organization_name": req_org.name if req_org else "",
        "requester_department_name": req_dept.name if req_dept else "",
        "reason": r.reason,
        "required_by": r.required_by,
        "message": r.message,
        "quantity": r.quantity,
        "status": r.status,
        "authority_notes": r.authority_notes,
        "scheduled_date": r.scheduled_date,
        "completed_date": r.completed_date,
        "created_at": r.created_at,
        "updated_at": r.updated_at,
    }


# ── Create request ────────────────────────────────────────────────

@router.post("", status_code=201)
def create_request(data: dict, db: Session = Depends(get_db)):
    """Submit a new resource transfer request."""
    resource_id = data.get("resource_id")
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    if resource.availability in ("disposed", "recycled", "transferred"):
        raise HTTPException(status_code=400, detail="This resource is no longer available for request.")

    # Check if already approved/transferred
    existing_active = db.query(ResourceRequest).filter(
        ResourceRequest.resource_id == resource_id,
        ResourceRequest.status.in_(["approved", "transfer_scheduled", "pending_owner_approval"]),
    ).first()
    if existing_active:
        raise HTTPException(status_code=400, detail="This resource already has an active request or transfer in progress.")

    rb = data.get("required_by")
    if rb and isinstance(rb, str):
        try:
            rb = datetime.fromisoformat(rb.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            rb = None

    req = ResourceRequest(
        request_id=_gen_request_id(db),
        resource_id=resource_id,
        requester_id=data.get("requester_id"),
        requester_organization_id=data["requester_organization_id"],
        requester_department_id=data["requester_department_id"],
        reason=data.get("reason", ""),
        required_by=rb,
        message=data.get("message", ""),
        quantity=data.get("quantity", 1),
        status="pending_owner_approval",
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return _enrich_request(req, db)


# ── Get single request ────────────────────────────────────────────

@router.get("/{request_pk}")
def get_request(request_pk: int, db: Session = Depends(get_db)):
    req = db.query(ResourceRequest).filter(ResourceRequest.id == request_pk).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return _enrich_request(req, db)


# ── My requests (as requester) ────────────────────────────────────

@router.get("/my/{user_id}")
def my_requests(user_id: int, db: Session = Depends(get_db)):
    reqs = (
        db.query(ResourceRequest)
        .filter(ResourceRequest.requester_id == user_id)
        .order_by(ResourceRequest.created_at.desc())
        .all()
    )
    return [_enrich_request(r, db) for r in reqs]


# ── Incoming requests (for authority — department) ─────────────────

@router.get("/incoming/{department_id}")
def incoming_requests(department_id: int, db: Session = Depends(get_db)):
    """Requests targeting resources owned by this department."""
    resource_ids = [r.id for r in db.query(Resource).filter(Resource.department_id == department_id).all()]
    if not resource_ids:
        return []
    reqs = (
        db.query(ResourceRequest)
        .filter(ResourceRequest.resource_id.in_(resource_ids))
        .order_by(ResourceRequest.created_at.desc())
        .all()
    )
    return [_enrich_request(r, db) for r in reqs]


# ── Approve ───────────────────────────────────────────────────────

@router.post("/{request_pk}/approve")
def approve_request(request_pk: int, data: dict = None, db: Session = Depends(get_db)):
    req = db.query(ResourceRequest).filter(ResourceRequest.id == request_pk).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != "pending_owner_approval":
        raise HTTPException(status_code=400, detail=f"Cannot approve — current status is '{req.status}'")

    # Safety check: resource still available
    resource = db.query(Resource).filter(Resource.id == req.resource_id).first()
    if not resource:
        raise HTTPException(status_code=400, detail="Resource no longer exists.")
    if resource.availability in ("disposed", "recycled", "transferred"):
        raise HTTPException(status_code=400, detail="This resource is no longer available.")
    if resource.availability == "maintenance":
        raise HTTPException(status_code=400, detail="This resource is currently under maintenance.")

    # Check no other approved request for same resource
    other = db.query(ResourceRequest).filter(
        ResourceRequest.resource_id == req.resource_id,
        ResourceRequest.id != req.id,
        ResourceRequest.status.in_(["approved", "transfer_scheduled"]),
    ).first()
    if other:
        raise HTTPException(status_code=400, detail="This resource is already reserved by another approved request.")

    req.status = "approved"
    req.authority_notes = (data or {}).get("notes", "")
    resource.availability = "reserved"
    db.commit()
    db.refresh(req)
    return _enrich_request(req, db)


# ── Reject ────────────────────────────────────────────────────────

@router.post("/{request_pk}/reject")
def reject_request(request_pk: int, data: dict = None, db: Session = Depends(get_db)):
    req = db.query(ResourceRequest).filter(ResourceRequest.id == request_pk).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != "pending_owner_approval":
        raise HTTPException(status_code=400, detail=f"Cannot reject — current status is '{req.status}'")

    req.status = "rejected"
    req.authority_notes = (data or {}).get("notes", "")
    db.commit()
    db.refresh(req)
    return _enrich_request(req, db)


# ── Schedule transfer ─────────────────────────────────────────────

@router.post("/{request_pk}/schedule-transfer")
def schedule_transfer(request_pk: int, data: dict = None, db: Session = Depends(get_db)):
    req = db.query(ResourceRequest).filter(ResourceRequest.id == request_pk).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != "approved":
        raise HTTPException(status_code=400, detail=f"Cannot schedule — current status is '{req.status}'")

    req.status = "transfer_scheduled"
    sd = (data or {}).get("scheduled_date")
    if sd and isinstance(sd, str):
        try:
            req.scheduled_date = datetime.fromisoformat(sd.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass
    elif sd:
        req.scheduled_date = sd
    db.commit()
    db.refresh(req)
    return _enrich_request(req, db)


# ── Complete transfer ─────────────────────────────────────────────

@router.post("/{request_pk}/complete-transfer")
def complete_transfer(request_pk: int, db: Session = Depends(get_db)):
    req = db.query(ResourceRequest).filter(ResourceRequest.id == request_pk).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != "transfer_scheduled":
        raise HTTPException(status_code=400, detail=f"Cannot complete — current status is '{req.status}'")

    req.status = "transferred"
    req.completed_date = datetime.utcnow()

    # Update resource ownership
    resource = db.query(Resource).filter(Resource.id == req.resource_id).first()
    if resource:
        resource.department_id = req.requester_department_id
        resource.organization_id = req.requester_organization_id
        resource.availability = "available"

    db.commit()
    db.refresh(req)
    return _enrich_request(req, db)


# ── Cancel (by requester) ────────────────────────────────────────

@router.post("/{request_pk}/cancel")
def cancel_request(request_pk: int, db: Session = Depends(get_db)):
    req = db.query(ResourceRequest).filter(ResourceRequest.id == request_pk).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status not in ("pending_owner_approval", "approved"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel — current status is '{req.status}'")

    # Release reserved status if it was approved
    if req.status == "approved":
        resource = db.query(Resource).filter(Resource.id == req.resource_id).first()
        if resource and resource.availability == "reserved":
            resource.availability = "available"

    req.status = "cancelled"
    db.commit()
    db.refresh(req)
    return _enrich_request(req, db)


# ── Contact message ──────────────────────────────────────────────

@router.post("/contact")
def send_contact(data: dict, db: Session = Depends(get_db)):
    """Send a contact message about a resource."""
    resource = db.query(Resource).filter(Resource.id == data.get("resource_id")).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    msg = ContactMessage(
        resource_id=data["resource_id"],
        sender_id=data.get("sender_id"),
        sender_name=data.get("sender_name", ""),
        sender_email=data.get("sender_email", ""),
        recipient_department_id=resource.department_id,
        subject=data.get("subject", f"Inquiry about {resource.name}"),
        message=data["message"],
    )
    db.add(msg)
    db.commit()
    return {"message": "Message sent to the resource authority.", "id": msg.id}
