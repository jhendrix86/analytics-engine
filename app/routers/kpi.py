"""
KPI router - real DB-backed CRUD. A KPI can optionally track a real
Metric by name (stored in extra_metadata, since the model itself has no
dedicated column for it) - POST /{kpi_id}/refresh pulls the latest real
observation of that metric into current_value, instead of the value
only ever being whatever was set at creation time.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.kpi import KPI
from app.models.metric import Metric
from app.models.tenant_base import apply_tenant_context

router = APIRouter()


class CreateKpiRequest(BaseModel):
    """Request to create a KPI"""
    name: str
    target: int
    description: Optional[str] = None
    metric_name: Optional[str] = None  # if given, current_value is pulled from that Metric's latest observation
    current_value: int = 0
    unit: Optional[str] = None
    period: str = "monthly"


def _status(progress: Optional[int]) -> Optional[str]:
    if progress is None:
        return None
    if progress >= 100:
        return "achieved"
    if progress >= 70:
        return "on_track"
    return "at_risk"


def _serialize(kpi: KPI) -> dict:
    return {
        "id": str(kpi.id),
        "name": kpi.name,
        "description": kpi.description,
        "metric_name": (kpi.extra_metadata or {}).get("metric_name"),
        "current_value": kpi.current_value,
        "target": kpi.target_value,
        "progress_percentage": kpi.progress_percentage,
        "status": _status(kpi.progress_percentage),
        "unit": kpi.unit,
        "period": kpi.period,
        "last_updated": kpi.last_updated.isoformat(),
    }


async def _get_kpi_or_404(db: AsyncSession, kpi_id: str) -> KPI:
    try:
        kpi_uuid = uuid.UUID(kpi_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"KPI '{kpi_id}' not found")

    kpi = await db.get(KPI, kpi_uuid)
    if kpi is None:
        raise HTTPException(status_code=404, detail=f"KPI '{kpi_id}' not found")
    return kpi


async def _latest_metric_value(db: AsyncSession, metric_name: str) -> Optional[int]:
    result = await db.execute(select(Metric.value).where(Metric.name == metric_name).order_by(Metric.timestamp.desc()).limit(1))
    row = result.first()
    return row[0] if row else None


@router.get("/")
async def list_kpis(db: AsyncSession = Depends(get_db)):
    """List all KPIs, real query"""
    result = await db.execute(select(KPI).order_by(KPI.name))
    kpis = result.scalars().all()
    return {"kpis": [_serialize(k) for k in kpis], "total": len(kpis)}


@router.post("/")
async def create_kpi(request: CreateKpiRequest, db: AsyncSession = Depends(get_db)):
    """Create a new KPI"""
    try:
        logger.info(f"Creating KPI: {request.name}")

        current_value = request.current_value
        if request.metric_name:
            latest = await _latest_metric_value(db, request.metric_name)
            if latest is not None:
                current_value = latest

        progress = round(100 * current_value / request.target) if request.target else None

        kpi = KPI(
            name=request.name,
            description=request.description,
            current_value=current_value,
            target_value=request.target,
            progress_percentage=progress,
            unit=request.unit,
            period=request.period,
            extra_metadata={"metric_name": request.metric_name} if request.metric_name else None,
        )
        apply_tenant_context(kpi)

        db.add(kpi)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=409, detail=f"A KPI named '{request.name}' already exists")
        await db.refresh(kpi)

        logger.info(f"KPI created: {kpi.id}")
        return _serialize(kpi)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create KPI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{kpi_id}/refresh")
async def refresh_kpi(kpi_id: str, db: AsyncSession = Depends(get_db)):
    """Pull the latest real observation of this KPI's tracked metric into current_value"""
    try:
        kpi = await _get_kpi_or_404(db, kpi_id)
        metric_name = (kpi.extra_metadata or {}).get("metric_name")
        if not metric_name:
            raise HTTPException(status_code=400, detail="This KPI has no metric_name to refresh from")

        latest = await _latest_metric_value(db, metric_name)
        if latest is None:
            raise HTTPException(status_code=404, detail=f"No recorded metric named '{metric_name}' to refresh from")

        kpi.current_value = latest
        kpi.progress_percentage = round(100 * latest / kpi.target_value) if kpi.target_value else None

        await db.commit()
        await db.refresh(kpi)

        logger.info(f"KPI refreshed: {kpi_id} -> {latest}")
        return _serialize(kpi)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh KPI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{kpi_id}")
async def get_kpi(kpi_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific KPI"""
    try:
        kpi = await _get_kpi_or_404(db, kpi_id)
        return _serialize(kpi)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get KPI: {e}")
        raise HTTPException(status_code=500, detail=str(e))
