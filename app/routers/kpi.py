"""
KPI router
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()


class CreateKpiRequest(BaseModel):
    """Request to create a KPI"""
    name: str
    metric: str
    target: float
    description: Optional[str] = None


@router.get("/")
async def list_kpis():
    """List all KPIs"""
    return {
        "kpis": [],
        "total": 0,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/")
async def create_kpi(request: CreateKpiRequest):
    """Create a new KPI"""
    return {
        "id": "kpi-1",
        "name": request.name,
        "metric": request.metric,
        "target": request.target,
        "description": request.description,
        "current_value": 0.0,
        "created_at": datetime.utcnow().isoformat()
    }


@router.get("/{kpi_id}")
async def get_kpi(kpi_id: str):
    """Get a specific KPI"""
    return {
        "id": kpi_id,
        "name": "KPI",
        "metric": "conversion_rate",
        "target": 0.05,
        "current_value": 0.03,
        "status": "on_track",
        "created_at": datetime.utcnow().isoformat()
    }
