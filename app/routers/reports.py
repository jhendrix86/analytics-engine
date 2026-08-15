"""
Reports router - real DB-backed CRUD, and POST /{id}/generate computes
a real aggregate over actually-recorded Metric rows instead of ever
claiming a PDF/CSV exists at a fake output_url. No file-generation or
storage infrastructure exists anywhere in this engine, so the honestly
computable output (real numbers, not a rendered document) is stored in
extra_metadata rather than fabricating output_url.
"""

import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.metric import Metric
from app.models.report import Report, ReportStatus
from app.models.tenant_base import apply_tenant_context

router = APIRouter()


class CreateReportRequest(BaseModel):
    """Request to create a report"""
    name: str
    description: Optional[str] = None
    report_type: str = "metrics_summary"
    metric_names: List[str] = []
    period_days: int = 30


def _serialize(report: Report) -> dict:
    return {
        "id": str(report.id),
        "name": report.name,
        "description": report.description,
        "report_type": report.report_type,
        "status": report.status.value,
        "config": report.config,
        "data": (report.extra_metadata or {}).get("results") if report.status == ReportStatus.COMPLETED else None,
        "error_message": report.error_message,
        "generated_at": report.generated_at.isoformat() if report.generated_at else None,
        "created_at": report.created_at.isoformat(),
    }


async def _get_report_or_404(db: AsyncSession, report_id: str) -> Report:
    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")

    report = await db.get(Report, report_uuid)
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
    return report


@router.get("/")
async def list_reports(db: AsyncSession = Depends(get_db)):
    """List all reports, real query"""
    result = await db.execute(select(Report).order_by(Report.created_at.desc()))
    reports = result.scalars().all()
    return {"reports": [_serialize(r) for r in reports], "total": len(reports)}


@router.post("/")
async def create_report(request: CreateReportRequest, db: AsyncSession = Depends(get_db)):
    """Create a new report, pending until /generate is called"""
    try:
        logger.info(f"Creating report: {request.name}")

        report = Report(
            name=request.name,
            description=request.description,
            report_type=request.report_type,
            status=ReportStatus.PENDING,
            config={"metric_names": request.metric_names, "period_days": request.period_days},
        )
        apply_tenant_context(report)

        db.add(report)
        await db.commit()
        await db.refresh(report)

        logger.info(f"Report created: {report.id}")
        return _serialize(report)

    except Exception as e:
        logger.error(f"Failed to create report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{report_id}/generate")
async def generate_report(report_id: str, db: AsyncSession = Depends(get_db)):
    """Actually compute the report's content from real recorded metrics"""
    try:
        report = await _get_report_or_404(db, report_id)
        logger.info(f"Generating report {report_id}")

        report.status = ReportStatus.GENERATING
        await db.flush()

        metric_names = (report.config or {}).get("metric_names") or []
        period_days = (report.config or {}).get("period_days", 30)
        since = datetime.utcnow() - timedelta(days=period_days)

        query = select(Metric).where(Metric.timestamp >= since)
        if metric_names:
            query = query.where(Metric.name.in_(metric_names))

        result = await db.execute(query)
        metrics = result.scalars().all()

        if not metrics:
            report.status = ReportStatus.FAILED
            report.error_message = "No metrics found matching this report's config in the given period"
            await db.commit()
            await db.refresh(report)
            return _serialize(report)

        by_name = {}
        for m in metrics:
            by_name.setdefault(m.name, []).append(m.value)

        results = {
            name: {"count": len(values), "latest": values[-1], "min": min(values), "max": max(values), "avg": round(sum(values) / len(values), 2)}
            for name, values in by_name.items()
        }

        report.status = ReportStatus.COMPLETED
        report.generated_at = datetime.utcnow()
        report.extra_metadata = {**(report.extra_metadata or {}), "results": results}

        await db.commit()
        await db.refresh(report)

        logger.info(f"Report generated: {report_id}")
        return _serialize(report)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}")
async def get_report(report_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific report"""
    try:
        report = await _get_report_or_404(db, report_id)
        return _serialize(report)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
