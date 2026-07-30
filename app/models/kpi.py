"""
KPI models
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class KPI(Base):
    """KPI model"""
    __tablename__ = "kpis"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # KPI details
    name = Column(String(255), nullable=False, unique=True)
    description = Column(String(500), nullable=True)
    
    # Current value
    current_value = Column(Integer, nullable=False)
    target_value = Column(Integer, nullable=True)
    
    # Progress
    progress_percentage = Column(Integer, default=0)
    
    # Context
    unit = Column(String(50), nullable=True)
    period = Column(String(50), default="monthly")  # daily, weekly, monthly, quarterly, yearly
    
    # Timestamps
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Relationships
    goals = relationship("KPIGoal", back_populates="kpi")
    
    def __repr__(self):
        return f"<KPI {self.name} - {self.current_value}/{self.target_value}>"


class KPIGoal(Base):
    """KPI goal model"""
    __tablename__ = "kpi_goals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kpi_id = Column(UUID(as_uuid=True), ForeignKey("kpis.id"), nullable=False)
    
    # Goal details
    target_value = Column(Integer, nullable=False)
    start_value = Column(Integer, nullable=False)
    
    # Period
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Status
    achieved = Column(Boolean, default=False)
    achieved_at = Column(DateTime, nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    kpi = relationship("KPI", back_populates="goals")
    
    def __repr__(self):
        return f"<KPIGoal {self.kpi_id} - {self.target_value}>"
