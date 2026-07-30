"""
Report models
"""

from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class ReportStatus(str, enum.Enum):
    """Report status enumeration"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Report(Base):
    """Report model"""
    __tablename__ = "reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Report details
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    report_type = Column(String(50), nullable=False)
    
    # Status
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING)
    
    # Configuration
    config = Column(JSON, nullable=False)  # Report configuration
    
    # Output
    output_url = Column(String(500), nullable=True)
    output_format = Column(String(20), default="pdf")  # pdf, csv, html
    
    # Schedule
    scheduled_at = Column(DateTime, nullable=True)
    generated_at = Column(DateTime, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Report {self.name} - {self.status}>"
