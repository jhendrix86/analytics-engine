"""
Verifies tenant context assignment for analytics-engine endpoints.
Tests that apply_tenant_context() correctly assigns tenant_id on create.
Note: Automatic query filtering is not yet implemented - this test validates
create-time tenant assignment only.
"""

from sqlalchemy import select

# Use fixed UUIDs that match what we create in conftest
TENANT_A = "3e2a7c54-a950-48f3-9eb9-d1eb6b2d1be2"
TENANT_B = "00000000-0000-0000-0000-000000000001"


async def test_apply_tenant_context_on_metric_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on metric creation."""
    from app.models.metric import Metric
    import uuid
    
    # Create metric for tenant A
    result = await client.post(
        "/metrics/custom",
        json={
            "name": "Test Metric",
            "value": 100.5,
            "unit": "count",
            "source_engine": "test-service"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert result.status_code == 200
    metric_id = result.json()["id"]
    
    # Verify tenant_id was correctly assigned
    metric = await db_session.get(Metric, uuid.UUID(metric_id))
    assert metric is not None
    assert str(metric.tenant_id) == TENANT_A


async def test_apply_tenant_context_on_dashboard_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on dashboard creation."""
    from app.models.dashboard import Dashboard
    import uuid
    
    # Create dashboard for tenant A
    result = await client.post(
        "/dashboards/",
        json={
            "name": "Test Dashboard",
            "description": "Test dashboard description"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert result.status_code == 200
    dashboard_id = result.json()["id"]
    
    # Verify dashboard tenant_id was correctly assigned
    dashboard = await db_session.get(Dashboard, uuid.UUID(dashboard_id))
    assert dashboard is not None
    assert str(dashboard.tenant_id) == TENANT_A


async def test_apply_tenant_context_on_report_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on report creation."""
    from app.models.report import Report
    import uuid
    
    # Create report for tenant A
    result = await client.post(
        "/reports/generate",
        json={
            "name": "Test Report",
            "query_config": {"metric_name": "test_metric"},
            "aggregation_type": "sum"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert result.status_code == 200
    report_id = result.json()["id"]
    
    # Verify report tenant_id was correctly assigned
    report = await db_session.get(Report, uuid.UUID(report_id))
    assert report is not None
    assert str(report.tenant_id) == TENANT_A


async def test_apply_tenant_context_on_kpi_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on KPI creation."""
    from app.models.kpi import KPI
    import uuid
    
    # Create metric for tenant A
    metric_result = await client.post(
        "/metrics/custom",
        json={
            "name": "Test Metric",
            "value": 100.5,
            "unit": "count",
            "source_engine": "test-service"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert metric_result.status_code == 200
    metric_id = metric_result.json()["id"]
    
    # Create KPI for tenant A
    kpi_result = await client.post(
        "/kpi/",
        json={
            "name": "Test KPI",
            "target_value": 1000,
            "metric_id": metric_id
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert kpi_result.status_code == 200
    kpi_id = kpi_result.json()["id"]
    
    # Verify KPI tenant_id was correctly assigned
    kpi = await db_session.get(KPI, uuid.UUID(kpi_id))
    assert kpi is not None
    assert str(kpi.tenant_id) == TENANT_A


async def test_apply_tenant_context_on_prediction_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on prediction creation."""
    from app.models.prediction import Prediction
    import uuid
    
    # Create metric for tenant A
    metric_result = await client.post(
        "/metrics/custom",
        json={
            "name": "Test Metric",
            "value": 100.5,
            "unit": "count",
            "source_engine": "test-service"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert metric_result.status_code == 200
    metric_id = metric_result.json()["id"]
    
    # Create prediction for tenant A
    prediction_result = await client.post(
        "/predictions/forecast",
        json={
            "metric_id": metric_id,
            "prediction_type": "forecast",
            "horizon_days": 7
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert prediction_result.status_code == 200
    prediction_id = prediction_result.json()["id"]
    
    # Verify prediction tenant_id was correctly assigned
    prediction = await db_session.get(Prediction, uuid.UUID(prediction_id))
    assert prediction is not None
    assert str(prediction.tenant_id) == TENANT_A
