"""
Analytics Engine smoke tests - validates router imports and basic endpoints
"""
import pytest
from datetime import datetime


@pytest.mark.asyncio
async def test_analytics_routers_import():
    """Verify all router modules import without error"""
    from app.routers import metrics, dashboards, reports, predictions, kpi
    assert hasattr(metrics, 'router')
    assert hasattr(dashboards, 'router')
    assert hasattr(reports, 'router')
    assert hasattr(predictions, 'router')
    assert hasattr(kpi, 'router')


@pytest.mark.asyncio
async def test_analytics_app_creation():
    """Verify FastAPI app instantiates without error"""
    from app.main import app
    assert app is not None
    assert app.title == "Analytics Engine"


@pytest.mark.asyncio
async def test_models_import():
    """Verify all data models import without error"""
    from app.models import Dashboard, KPI, Metric, Prediction, Report
    assert Dashboard is not None
    assert KPI is not None
    assert Metric is not None
    assert Prediction is not None
    assert Report is not None
