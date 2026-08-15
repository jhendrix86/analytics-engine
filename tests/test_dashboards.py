"""dashboards.py is now real: dashboards/widgets hit real tables; widget creation didn't exist at all before."""


async def _create_dashboard(client, **overrides):
    payload = {"name": "Revenue Overview", "description": "Top-line metrics"}
    payload.update(overrides)
    r = await client.post("/dashboards/", json=payload)
    assert r.status_code == 200
    return r.json()


async def test_create_dashboard_persists_a_real_row(client):
    body = await _create_dashboard(client)
    assert body["name"] == "Revenue Overview"
    assert body["widgets"] == []
    assert body["id"]  # a real generated UUID, not "dashboard-1"


async def test_create_dashboard_rejects_duplicate_name_within_the_same_tenant(client):
    # The uniqueness constraint is (tenant_id, name) - with no tenant
    # header, tenant_id is NULL on every row, and SQL NULLs never equal
    # each other, so the constraint needs a real, matching tenant on both
    # calls to actually be exercised.
    headers = {"X-Tenant-ID": "11111111-1111-1111-1111-111111111111"}
    await client.post("/dashboards/", json={"name": "Revenue Overview"}, headers=headers)
    r = await client.post("/dashboards/", json={"name": "Revenue Overview"}, headers=headers)
    assert r.status_code == 409


async def test_create_widget_persists_a_real_row(client):
    dashboard = await _create_dashboard(client)

    r = await client.post(f"/dashboards/{dashboard['id']}/widgets", json={
        "widget_type": "chart", "title": "MRR Trend", "data_source": "mrr",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "MRR Trend"
    assert body["data_source"] == "mrr"


async def test_create_widget_for_unknown_dashboard_is_a_real_404(client):
    r = await client.post("/dashboards/00000000-0000-0000-0000-000000000000/widgets", json={"widget_type": "chart", "title": "x"})
    assert r.status_code == 404


async def test_get_dashboard_returns_the_real_row_with_real_widgets(client):
    dashboard = await _create_dashboard(client)
    await client.post(f"/dashboards/{dashboard['id']}/widgets", json={"widget_type": "chart", "title": "MRR Trend"})

    r = await client.get(f"/dashboards/{dashboard['id']}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == dashboard["id"]
    assert len(body["widgets"]) == 1


async def test_get_unknown_dashboard_is_a_real_404(client):
    r = await client.get("/dashboards/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_list_dashboards_reflects_real_created_rows(client):
    await _create_dashboard(client, name="one")
    await _create_dashboard(client, name="two")

    r = await client.get("/dashboards/")
    body = r.json()
    assert body["total"] == 2
