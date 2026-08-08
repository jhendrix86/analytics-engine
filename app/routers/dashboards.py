"""
Dashboards router
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()


class CreateDashboardRequest(BaseModel):
    """Request to create a dashboard"""
    name: str
    description: Optional[str] = None


@router.get("/")
async def list_dashboards():
    """List all dashboards"""
    return {
        "dashboards": [],
        "total": 0,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/")
async def create_dashboard(request: CreateDashboardRequest):
    """Create a new dashboard"""
    return {
        "id": "dashboard-1",
        "name": request.name,
        "description": request.description,
        "created_at": datetime.utcnow().isoformat()
    }


@router.get("/{dashboard_id}")
async def get_dashboard(dashboard_id: str):
    """Get a specific dashboard"""
    return {
        "id": dashboard_id,
        "name": "Dashboard",
        "widgets": [],
        "created_at": datetime.utcnow().isoformat()
    }
