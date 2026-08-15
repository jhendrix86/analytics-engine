"""
Dashboards router - real DB-backed CRUD against dashboards/widgets.
Also adds POST /{dashboard_id}/widgets, which didn't exist at all
before - Widget was a real model with a real dashboard FK and nothing
could ever create one via the API (same recurring gap found in every
other mock engine this session).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import Optional
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.dashboard import Dashboard, Widget
from app.models.tenant_base import apply_tenant_context

router = APIRouter()


class CreateDashboardRequest(BaseModel):
    """Request to create a dashboard"""
    name: str
    description: Optional[str] = None
    layout: dict = {}


class CreateWidgetRequest(BaseModel):
    """Request to add a widget to a dashboard"""
    widget_type: str
    title: str
    config: dict = {}
    data_source: Optional[str] = None
    query_config: Optional[dict] = None
    position_x: int = 0
    position_y: int = 0
    width: int = 4
    height: int = 3


def _serialize_widget(widget: Widget) -> dict:
    return {
        "id": str(widget.id),
        "widget_type": widget.widget_type,
        "title": widget.title,
        "config": widget.config,
        "data_source": widget.data_source,
        "query_config": widget.query_config,
        "position": {"x": widget.position_x, "y": widget.position_y, "width": widget.width, "height": widget.height},
    }


def _serialize_dashboard(dashboard: Dashboard, widgets: Optional[list] = None) -> dict:
    return {
        "id": str(dashboard.id),
        "name": dashboard.name,
        "description": dashboard.description,
        "layout": dashboard.layout,
        "is_active": dashboard.is_active,
        "access_level": dashboard.access_level,
        "widgets": [_serialize_widget(w) for w in widgets] if widgets is not None else None,
        "created_at": dashboard.created_at.isoformat(),
    }


async def _get_dashboard_or_404(db: AsyncSession, dashboard_id: str) -> Dashboard:
    try:
        dashboard_uuid = uuid.UUID(dashboard_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Dashboard '{dashboard_id}' not found")

    dashboard = await db.get(Dashboard, dashboard_uuid)
    if dashboard is None:
        raise HTTPException(status_code=404, detail=f"Dashboard '{dashboard_id}' not found")
    return dashboard


@router.get("/")
async def list_dashboards(db: AsyncSession = Depends(get_db)):
    """List all dashboards, real query"""
    result = await db.execute(select(Dashboard).order_by(Dashboard.created_at.desc()))
    dashboards = result.scalars().all()

    return {"dashboards": [_serialize_dashboard(d) for d in dashboards], "total": len(dashboards)}


@router.post("/")
async def create_dashboard(request: CreateDashboardRequest, db: AsyncSession = Depends(get_db)):
    """Create a new dashboard"""
    try:
        logger.info(f"Creating dashboard: {request.name}")

        dashboard = Dashboard(name=request.name, description=request.description, layout=request.layout)
        apply_tenant_context(dashboard)

        db.add(dashboard)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=409, detail=f"A dashboard named '{request.name}' already exists")
        await db.refresh(dashboard)

        logger.info(f"Dashboard created: {dashboard.id}")
        return _serialize_dashboard(dashboard, widgets=[])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{dashboard_id}/widgets")
async def create_widget(dashboard_id: str, request: CreateWidgetRequest, db: AsyncSession = Depends(get_db)):
    """Add a widget to a dashboard"""
    try:
        dashboard = await _get_dashboard_or_404(db, dashboard_id)

        widget = Widget(
            dashboard_id=dashboard.id,
            widget_type=request.widget_type,
            title=request.title,
            config=request.config,
            data_source=request.data_source,
            query_config=request.query_config,
            position_x=request.position_x,
            position_y=request.position_y,
            width=request.width,
            height=request.height,
        )
        apply_tenant_context(widget)

        db.add(widget)
        await db.commit()
        await db.refresh(widget)

        logger.info(f"Widget created: {widget.id} on dashboard {dashboard_id}")
        return _serialize_widget(widget)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create widget: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dashboard_id}")
async def get_dashboard(dashboard_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific dashboard, real query, real widgets included"""
    try:
        dashboard = await _get_dashboard_or_404(db, dashboard_id)

        widgets_result = await db.execute(select(Widget).where(Widget.dashboard_id == dashboard.id))
        widgets = widgets_result.scalars().all()

        return _serialize_dashboard(dashboard, widgets=widgets)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))
