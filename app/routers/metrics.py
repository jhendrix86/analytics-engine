"""
Metrics router - real DB-backed ingestion and aggregation against the
metrics table. POST /custom is the real ingestion point other engines
(or an ops process) push data into; GET /real-time and GET /historical
read and aggregate what's actually been recorded, instead of fixed
literals.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.metric import Metric, MetricType
from app.models.tenant_base import apply_tenant_context

router = APIRouter()


class CreateCustomMetricRequest(BaseModel):
    """Request to record a metric observation"""
    name: str
    metric_type: MetricType
    value: int
    unit: Optional[str] = None
    source_engine: Optional[str] = None


def _serialize(metric: Metric) -> dict:
    change = None
    if metric.previous_value is not None and metric.previous_value != 0:
        change = round(100 * (metric.value - metric.previous_value) / metric.previous_value, 1)

    return {
        "id": str(metric.id),
        "name": metric.name,
        "metric_type": metric.metric_type.value,
        "description": metric.description,
        "value": metric.value,
        "previous_value": metric.previous_value,
        "change_pct": change,
        "unit": metric.unit,
        "source_engine": metric.source_engine,
        "timestamp": metric.timestamp.isoformat(),
        "created_at": metric.created_at.isoformat(),
    }


@router.get("/real-time")
async def get_real_time_metrics(db: AsyncSession = Depends(get_db)):
    """Real latest-observation-per-metric-name snapshot, computed from actually-recorded metrics"""
    try:
        logger.info("Getting real-time metrics")

        result = await db.execute(select(Metric).order_by(Metric.timestamp.desc()))
        all_metrics = result.scalars().all()

        latest_by_name = {}
        for metric in all_metrics:
            if metric.name not in latest_by_name:
                latest_by_name[metric.name] = metric

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {name: _serialize(m) for name, m in latest_by_name.items()},
        }

    except Exception as e:
        logger.error(f"Failed to get real-time metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/historical")
async def get_historical_metrics(
    metric_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """Real time-series query against recorded metrics"""
    try:
        logger.info("Getting historical metrics")

        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        query = select(Metric).where(Metric.timestamp >= start_date, Metric.timestamp <= end_date)
        if metric_name is not None:
            query = query.where(Metric.name == metric_name)

        result = await db.execute(query.order_by(Metric.timestamp))
        metrics = result.scalars().all()

        return {
            "metric_name": metric_name,
            "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
            "data": [_serialize(m) for m in metrics],
        }

    except Exception as e:
        logger.error(f"Failed to get historical metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/custom")
async def create_custom_metric(request: CreateCustomMetricRequest, db: AsyncSession = Depends(get_db)):
    """Record a metric observation - the real ingestion point other engines push data into"""
    try:
        logger.info(f"Creating custom metric: {request.name}")

        prior_result = await db.execute(
            select(Metric).where(Metric.name == request.name).order_by(Metric.timestamp.desc()).limit(1)
        )
        prior = prior_result.scalars().first()

        metric = Metric(
            name=request.name,
            metric_type=request.metric_type,
            value=request.value,
            previous_value=prior.value if prior else None,
            unit=request.unit,
            source_engine=request.source_engine,
        )
        apply_tenant_context(metric)

        db.add(metric)
        await db.commit()
        await db.refresh(metric)

        logger.info(f"Custom metric created: {metric.id}")
        return _serialize(metric)

    except Exception as e:
        logger.error(f"Failed to create custom metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))
