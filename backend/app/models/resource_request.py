"""Resource Request model — full transfer-request workflow."""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class ResourceRequest(Base):
    __tablename__ = "resource_requests"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(50), unique=True, nullable=False)  # REQ-2026-NNNNN

    # Resource being requested
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)

    # Requester info
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    requester_organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    requester_department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

    # Request details
    reason = Column(Text)
    required_by = Column(DateTime(timezone=True), nullable=True)
    message = Column(Text)
    quantity = Column(Integer, default=1)

    # Workflow status
    # pending_owner_approval | approved | rejected | transfer_scheduled | transferred | cancelled
    status = Column(String(50), default="pending_owner_approval")

    # Authority notes
    authority_notes = Column(Text)
    scheduled_date = Column(DateTime(timezone=True), nullable=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    resource = relationship("Resource", foreign_keys=[resource_id])
    requester = relationship("User", foreign_keys=[requester_id])
    requester_organization = relationship("Organization", foreign_keys=[requester_organization_id])
    requester_department = relationship("Department", foreign_keys=[requester_department_id])


class ContactMessage(Base):
    """Simple internal contact / message for resource inquiries."""
    __tablename__ = "contact_messages"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    sender_name = Column(String(255))
    sender_email = Column(String(255))
    recipient_department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    subject = Column(String(255))
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
