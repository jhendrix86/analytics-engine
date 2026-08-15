"""
Metric models
"""

from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base
from app.models.tenant_base import TenantBase


class MetricType(str, enum.Enum):
    """Metric type enumeration"""
    REVENUE = "revenue"
    USER = "user"
    MARKETING = "marketing"
    SALES = "sales"
    SUPPORT = "support"
    OPERATIONAL = "operational"


class Metric(TenantBase, Base):
    """Metric model"""
    __tablename__ = "metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metric details - NOT unique: a metric is a time series, the same
    # name legitimately gets a new row per observation. A global unique
    # constraint here would make it impossible to ever record a second
    # data point for the same metric - a real, blocking bug, found and
    # fixed before this engine could work as a metrics store at all.
    name = Column(String(255), nullable=False, index=True)
    metric_type = Column(Enum(MetricType), nullable=False)
    description = Column(String(500), nullable=True)
    
    # Value
    value = Column(Integer, nullable=False)
    previous_value = Column(Integer, nullable=True)
    
    # Context
    unit = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Source
    source_engine = Column(String(100), nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Metric {self.name} - {self.value}>"
