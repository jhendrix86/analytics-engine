"""
Reports router
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()


class CreateReportRequest(BaseModel):
    """Request to create a report"""
    name: str
    description: Optional[str] = None


@router.get("/")
async def list_reports():
    """List all reports"""
    return {
        "reports": [],
        "total": 0,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/")
async def create_report(request: CreateReportRequest):
    """Create a new report"""
    return {
        "id": "report-1",
        "name": request.name,
        "description": request.description,
        "created_at": datetime.utcnow().isoformat()
    }


@router.get("/{report_id}")
async def get_report(report_id: str):
    """Get a specific report"""
    return {
        "id": report_id,
        "name": "Report",
        "data": {},
        "created_at": datetime.utcnow().isoformat()
    }
