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
            "value": 100.5,
            "unit": "count",
            "source_engine": "test-service"
        },
        headers={"X-Tenant-ID": tenant_id},
    )
    assert resp.status_code == 200
    return resp.json()["id"]


async def test_tenant_cannot_read_another_tenants_metric(client):
    metric_id = await _create_metric(client, TENANT_A, "Tenant A's Metric")

    same_tenant = await client.get(f"/metrics/{metric_id}", headers={"X-Tenant-ID": TENANT_A})
    assert same_tenant.status_code == 200

    other_tenant = await client.get(f"/metrics/{metric_id}", headers={"X-Tenant-ID": TENANT_B})
    assert other_tenant.status_code == 404


async def test_list_metrics_is_scoped_per_tenant(client):
    await _create_metric(client, TENANT_A, "A's Metric 1")
    await _create_metric(client, TENANT_A, "A's Metric 2")
    await _create_metric(client, TENANT_B, "B's Metric")

    a_listing = await client.get("/metrics/", headers={"X-Tenant-ID": TENANT_A})
    assert a_listing.status_code == 200
    assert a_listing.json()["total"] == 2

    b_listing = await client.get("/metrics/", headers={"X-Tenant-ID": TENANT_B})
    assert b_listing.status_code == 200
    assert b_listing.json()["total"] == 1


async def test_no_tenant_header_sees_everything(client):
    """Fail-open posture: no X-Tenant-ID means no filtering is applied."""
    await _create_metric(client, TENANT_A, "A's Metric")
    await _create_metric(client, TENANT_B, "B's Metric")

    unscoped = await client.get("/metrics/")
    assert unscoped.status_code == 200
    assert unscoped.json()["total"] == 2


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
        "/reports/generate",
        json={
            "name": "Test Report",
            "query_config": {"metric_name": "test_metric"},
            "aggregation_type": "sum"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert report_resp.status_code == 200
    report_id = report_resp.json()["id"]

    # Tenant A can see the report
    a_report = await client.get(f"/reports/{report_id}", headers={"X-Tenant-ID": TENANT_A})
    assert a_report.status_code == 200

    # Tenant B cannot see the report
    b_report = await client.get(f"/reports/{report_id}", headers={"X-Tenant-ID": TENANT_B})
    assert b_report.status_code == 404


async def test_kpi_creation_respects_tenant_scoping(client):
    """KPI creation should be tenant-scoped."""
    metric_id = await _create_metric(client, TENANT_A, "Test Metric")

    # Create KPI for tenant A
    kpi_resp = await client.post(
        "/kpi/",
        json={
            "name": "Test KPI",
            "target_value": 1000,
            "metric_id": metric_id
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert kpi_resp.status_code == 200
    kpi_id = kpi_resp.json()["id"]

    # Tenant A can see the KPI
    a_kpi = await client.get(f"/kpi/{kpi_id}", headers={"X-Tenant-ID": TENANT_A})
    assert a_kpi.status_code == 200

    # Tenant B cannot see the KPI
    b_kpi = await client.get(f"/kpi/{kpi_id}", headers={"X-Tenant-ID": TENANT_B})
    assert b_kpi.status_code == 404
