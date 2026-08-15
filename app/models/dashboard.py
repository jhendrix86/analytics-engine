"""
Dashboard models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base
from app.models.tenant_base import TenantBase


class Dashboard(TenantBase, Base):
    """Dashboard model"""
    __tablename__ = "dashboards"
    __table_args__ = (
        # Unique per-tenant, not globally - a global unique name would let
        # one tenant block every other tenant from ever using "Sales Overview".
        UniqueConstraint("tenant_id", "name", name="uq_dashboards_tenant_name"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Dashboard details
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    
    # Layout
    layout = Column(JSON, nullable=False)  # Widget layout configuration
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Access
    access_level = Column(String(50), default="admin")  # admin, user, readonly
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    widgets = relationship("Widget", back_populates="dashboard", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Dashboard {self.name}>"


class Widget(TenantBase, Base):
    """Widget model"""
    __tablename__ = "widgets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id = Column(UUID(as_uuid=True), ForeignKey("dashboards.id"), nullable=False)
    
    # Widget details
    widget_type = Column(String(50), nullable=False)  # chart, metric, table, etc.
    title = Column(String(255), nullable=False)
    
    # Configuration
    config = Column(JSON, nullable=False)  # Widget-specific configuration
    
    # Position
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    width = Column(Integer, default=4)
    height = Column(Integer, default=3)
    
    # Data source
    data_source = Column(String(100), nullable=True)
    query_config = Column(JSON, nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dashboard = relationship("Dashboard", back_populates="widgets")
    
    def __repr__(self):
        return f"<Widget {self.title} - {self.widget_type}>"
