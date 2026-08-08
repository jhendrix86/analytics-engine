"""
Metrics router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

from app.database import get_db

router = APIRouter()


class CreateCustomMetricRequest(BaseModel):
    """Request to create a custom metric"""
    name: str
    metric_type: str
    value: int
    unit: Optional[str] = None


@router.get("/real-time")
async def get_real_time_metrics(
    db: AsyncSession = Depends(get_db)
):
    """Get real-time metrics"""
    try:
        logger.info("Getting real-time metrics")
        
        # In production, this would query from database
        # For now, return a mock response
        metrics = {
            "revenue": {
                "current": 29100,
                "previous": 25000,
                "change": 16.4,
                "unit": "USD"
            },
            "users": {
                "current": 1500,
                "previous": 1200,
                "change": 25.0,
                "unit": "count"
            },
            "mrr": {
                "current": 25000,
                "previous": 22000,
                "change": 13.6,
                "unit": "USD"
            },
            "churn_rate": {
                "current": 2.5,
                "previous": 3.0,
                "change": -16.7,
                "unit": "percentage"
            }
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get real-time metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/historical")
async def get_historical_metrics(
    metric_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get historical metrics"""
    try:
        logger.info("Getting historical metrics")
        
        # Set default date range (last 30 days)
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = datetime.utcnow().isoformat()
        
        # In production, this would query from database
        # For now, return a mock response
        data = [
            {"date": "2024-01-01", "revenue": 970, "users": 45},
            {"date": "2024-01-02", "revenue": 1455, "users": 52},
            {"date": "2024-01-03", "revenue": 970, "users": 38}
        ]
        
        return {
            "metric_name": metric_name,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "data": data
        }
        
    except Exception as e:
        logger.error(f"Failed to get historical metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/custom")
async def create_custom_metric(
    request: CreateCustomMetricRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create custom metric"""
    try:
        logger.info(f"Creating custom metric: {request.name}")

        # In production, this would save to database
        # For now, return a mock response
        metric = {
            "id": "metric_123",
            "name": request.name,
            "metric_type": request.metric_type,
            "value": request.value,
            "unit": request.unit,
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Custom metric created: {metric['id']}")
        return metric
        
    except Exception as e:
        logger.error(f"Failed to create custom metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))
