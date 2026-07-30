"""
Prediction models
"""

from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from app.database import Base


class PredictionType(str, enum.Enum):
    """Prediction type enumeration"""
    FORECAST = "forecast"
    CLASSIFICATION = "classification"
    ANOMALY = "anomaly"
    REGRESSION = "regression"


class Prediction(Base):
    """Prediction model"""
    __tablename__ = "predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Prediction details
    name = Column(String(255), nullable=False)
    prediction_type = Column(Enum(PredictionType), nullable=False)
    
    # Model
    model_name = Column(String(100), nullable=True)
    model_version = Column(String(50), nullable=True)
    
    # Input
    input_data = Column(JSON, nullable=False)
    
    # Output
    prediction = Column(JSON, nullable=False)
    confidence = Column(Integer, nullable=True)  # percentage
    
    # Timestamps
    predicted_at = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<Prediction {self.name} - {self.prediction_type}>"
