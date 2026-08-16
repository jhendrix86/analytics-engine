"""
Verifies tenant isolation for analytics-engine endpoints.
Tests that automatic query filtering actually isolates data between tenants.
"""

# Use fixed UUIDs that match what we create in conftest
TENANT_A = "3e2a7c54-a950-48f3-9eb9-d1eb6b2d1be2"
TENANT_B = "00000000-0000-0000-0000-000000000001"


async def _create_metric(client, tenant_id, name):
    resp = await client.post(
        "/metrics/custom",
        json={
            "name": name,
            "metric_type": "operational",
            "value": 100,
            "unit": "count",
            "source_engine": "test-service"
        },
        headers={"X-Tenant-ID": tenant_id},
    )
    assert resp.status_code == 200
    return resp.json()["id"]


async def test_tenant_cannot_read_another_tenants_metric(client):
    await _create_metric(client, TENANT_A, "Tenant A's Metric")

    # Verify tenant A can see the metric in real-time metrics
    a_metrics = await client.get("/metrics/real-time", headers={"X-Tenant-ID": TENANT_A})
    assert a_metrics.status_code == 200
    assert "Tenant A's Metric" in a_metrics.json()["metrics"]

    # Verify tenant B cannot see the metric
    b_metrics = await client.get("/metrics/real-time", headers={"X-Tenant-ID": TENANT_B})
    assert b_metrics.status_code == 200
    assert "Tenant A's Metric" not in b_metrics.json()["metrics"]


async def test_list_metrics_is_scoped_per_tenant(client):
    await _create_metric(client, TENANT_A, "A's Metric 1")
    await _create_metric(client, TENANT_A, "A's Metric 2")
    
    # Verify tenant A sees their metrics
    a_metrics = await client.get("/metrics/real-time", headers={"X-Tenant-ID": TENANT_A})
    assert a_metrics.status_code == 200
    assert len(a_metrics.json()["metrics"]) == 2


async def test_no_tenant_header_sees_everything(client):
    """Fail-open posture: no X-Tenant-ID means no filtering is applied."""
    await _create_metric(client, TENANT_A, "A's Metric")
    
    # Verify no-tenant header sees the metric
    unscoped = await client.get("/metrics/real-time")
    assert unscoped.status_code == 200
    assert len(unscoped.json()["metrics"]) == 1


async def test_dashboard_creation_respects_tenant_scoping(client):
    """Dashboard creation should be tenant-scoped."""
    # Create dashboard for tenant A
    dashboard_resp = await client.post(
        "/dashboards/",
        json={
            "name": "Test Dashboard",
            "description": "Test dashboard description"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert dashboard_resp.status_code == 200
    dashboard_id = dashboard_resp.json()["id"]

    # Tenant A can see the dashboard
    a_dashboard = await client.get(f"/dashboards/{dashboard_id}", headers={"X-Tenant-ID": TENANT_A})
    assert a_dashboard.status_code == 200

    # Tenant B cannot see the dashboard
    b_dashboard = await client.get(f"/dashboards/{dashboard_id}", headers={"X-Tenant-ID": TENANT_B})
    assert b_dashboard.status_code == 404


async def test_report_generation_respects_tenant_scoping(client):
    """Report generation should be tenant-scoped."""
    # Create report for tenant A
    report_resp = await client.post(
        "/reports/",
        json={
            "name": "Test Report",
            "report_type": "summary",
            "metric_names": ["test_metric"],
            "period_days": 30
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert report_resp.status_code == 200
    report_id = report_resp.json()["id"]

    # Tenant A can see the report
    a_reports = await client.get("/reports/", headers={"X-Tenant-ID": TENANT_A})
    assert a_reports.status_code == 200
    assert a_reports.json()["total"] == 1

    # Tenant B cannot see the report
    b_reports = await client.get("/reports/", headers={"X-Tenant-ID": TENANT_B})
    assert b_reports.status_code == 200
    assert b_reports.json()["total"] == 0


async def test_kpi_creation_respects_tenant_scoping(client):
    """KPI creation should be tenant-scoped."""
    # Create KPI for tenant A
    kpi_resp = await client.post(
        "/kpi/",
        json={
            "name": "Test KPI",
            "target": 1000,
            "current_value": 500,
            "unit": "users",
            "period": "monthly"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert kpi_resp.status_code == 200

    # Tenant A can see the KPI
    a_kpis = await client.get("/kpi/", headers={"X-Tenant-ID": TENANT_A})
    assert a_kpis.status_code == 200
    assert a_kpis.json()["total"] == 1

    # Tenant B cannot see the KPI
    b_kpis = await client.get("/kpi/", headers={"X-Tenant-ID": TENANT_B})
    assert b_kpis.status_code == 200
    assert b_kpis.json()["total"] == 0
