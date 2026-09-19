"""Match model for resource matching results."""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from app.database.connection import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("resource_requests.id"), nullable=False)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)
    compatibility_score = Column(Float, default=0)
    condition_score = Column(Float, default=0)
    availability_score = Column(Float, default=0)
    underutilization_score = Column(Float, default=0)
    logistics_score = Column(Float, default=0)
    remaining_life_score = Column(Float, default=0)
    overall_score = Column(Float, default=0)
    explanation = Column(Text)
    match_details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
