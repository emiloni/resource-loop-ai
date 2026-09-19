"""Resource Transfer model."""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class ResourceTransfer(Base):
    __tablename__ = "resource_transfers"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)
    from_organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    from_department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    to_organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    to_department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="requested")
    reason = Column(Text)
    notes = Column(Text)
    scheduled_date = Column(DateTime(timezone=True), nullable=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    resource = relationship("Resource", back_populates="transfers")
