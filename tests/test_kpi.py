"""kpi.py is now real: KPIs hit real tables, /refresh pulls a real Metric observation into current_value."""


async def _create_kpi(client, **overrides):
    payload = {"name": "Signup Conversion", "target": 100}
    payload.update(overrides)
    r = await client.post("/kpi/", json=payload)
    assert r.status_code == 200
    return r.json()


async def test_create_kpi_persists_a_real_row(client):
    body = await _create_kpi(client, current_value=30)
    assert body["name"] == "Signup Conversion"
    assert body["current_value"] == 30
    assert body["progress_percentage"] == 30
    assert body["status"] == "at_risk"
    assert body["id"]  # a real generated UUID, not "kpi-1"


async def test_create_kpi_rejects_duplicate_name_within_the_same_tenant(client):
    # Same NULL-tenant caveat as dashboards.py's equivalent test - the
    # constraint is (tenant_id, name), so it needs a real, matching
    # tenant on both calls to actually be exercised.
    headers = {"X-Tenant-ID": "11111111-1111-1111-1111-111111111111"}
    await client.post("/kpi/", json={"name": "Signup Conversion", "target": 100}, headers=headers)
    r = await client.post("/kpi/", json={"name": "Signup Conversion", "target": 50}, headers=headers)
    assert r.status_code == 409


async def test_create_kpi_with_metric_name_pulls_real_current_value(client):
    await client.post("/metrics/custom", json={"name": "conversions", "metric_type": "sales", "value": 42})

    body = await _create_kpi(client, name="Conversions KPI", metric_name="conversions", target=100)
    assert body["current_value"] == 42
    assert body["metric_name"] == "conversions"


async def test_refresh_kpi_pulls_the_latest_real_observation(client):
    await client.post("/metrics/custom", json={"name": "conversions", "metric_type": "sales", "value": 42})
    kpi = await _create_kpi(client, name="Conversions KPI", metric_name="conversions", target=100)

    await client.post("/metrics/custom", json={"name": "conversions", "metric_type": "sales", "value": 80})
    r = await client.post(f"/kpi/{kpi['id']}/refresh")

    assert r.status_code == 200
    body = r.json()
    assert body["current_value"] == 80
    assert body["progress_percentage"] == 80
    assert body["status"] == "on_track"


async def test_refresh_kpi_without_a_tracked_metric_is_rejected(client):
    kpi = await _create_kpi(client)
    r = await client.post(f"/kpi/{kpi['id']}/refresh")
    assert r.status_code == 400


async def test_refresh_unknown_kpi_is_a_real_404(client):
    r = await client.post("/kpi/00000000-0000-0000-0000-000000000000/refresh")
    assert r.status_code == 404


async def test_get_unknown_kpi_is_a_real_404(client):
    r = await client.get("/kpi/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_list_kpis_reflects_real_created_rows(client):
    await _create_kpi(client, name="one")
    await _create_kpi(client, name="two")

    r = await client.get("/kpi/")
    assert r.json()["total"] == 2
