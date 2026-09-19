"""Resource Image model."""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class ResourceImage(Base):
    __tablename__ = "resource_images"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)
    image_url = Column(String(500), nullable=False)
    filename = Column(String(255))
    is_primary = Column(Integer, default=0)
    ai_analysis = Column(Text)
    ai_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    resource = relationship("Resource", back_populates="images")
