"""Import Session model — tracks CSV/Excel import lifecycle."""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.database.connection import Base


class ImportSession(Base):
    __tablename__ = "import_sessions"

    id = Column(Integer, primary_key=True, index=True)
    import_id = Column(String(50), unique=True, nullable=False)  # IMP-2026-NNNNN
    organization_id = Column(Integer, nullable=False)
    filename = Column(String(255))
    status = Column(String(50), default="pending")  # pending | completed | failed
    total_rows = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    invalid_rows = Column(Integer, default=0)
    created_count = Column(Integer, default=0)
    skipped_count = Column(Integer, default=0)
    errors_json = Column(JSON, default=list)
    validated_data_json = Column(JSON, default=dict)  # Serialized validated rows
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
