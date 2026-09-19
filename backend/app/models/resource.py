"""Resource model - core entity."""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(50), unique=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    category = Column(String(100), nullable=False)
    type = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    condition = Column(String(50))
    availability = Column(String(50), default="available")
    utilization = Column(Integer, default=0)
    status = Column(String(50), default="active")
    location = Column(String(255))
    building = Column(String(255))
    room = Column(String(100))
    purchase_date = Column(DateTime(timezone=True), nullable=True)
    remaining_useful_life_months = Column(Integer)
    warranty_expiry = Column(DateTime(timezone=True), nullable=True)
    specifications = Column(JSON, default={})
    share_scope = Column(String(50), default="organization")
    original_cost = Column(Float, nullable=True)
    estimated_current_value = Column(Float, nullable=True)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization", back_populates="resources")
    department = relationship("Department", back_populates="resources")
    owner = relationship("User", back_populates="resources_owned", foreign_keys=[owner_id])
    images = relationship("ResourceImage", back_populates="resource")
    transfers = relationship("ResourceTransfer", back_populates="resource", foreign_keys="ResourceTransfer.resource_id")
