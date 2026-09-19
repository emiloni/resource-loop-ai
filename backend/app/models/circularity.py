"""Circularity Assessment model."""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from app.database.connection import Base


class CircularityAssessment(Base):
    __tablename__ = "circularity_assessments"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    assessed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    input_type = Column(String(50))
    input_data = Column(Text)
    detected_object = Column(String(255))
    detected_material = Column(String(255))
    detected_condition = Column(String(50))
    detected_damage = Column(Text)
    repairability = Column(String(50))
    structural_integrity = Column(String(50))
    estimated_remaining_life_months = Column(Integer)
    note = Column(Text)
    recommendations = Column(JSON)
    recommended_action = Column(String(50))
    recommended_explanation = Column(Text)
    confidence = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
