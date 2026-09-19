"""Impact Record model."""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.sql import func
from app.database.connection import Base


class ImpactRecord(Base):
    __tablename__ = "impact_records"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    resources_reused = Column(Integer, default=0)
    resources_repaired = Column(Integer, default=0)
    resources_redistributed = Column(Integer, default=0)
    resources_recycled = Column(Integer, default=0)
    purchases_avoided = Column(Integer, default=0)
    cost_avoided = Column(Float, default=0)
    waste_avoided_kg = Column(Float, default=0)
    co2_saved_kg = Column(Float, default=0)
    period = Column(String(50))
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text)
