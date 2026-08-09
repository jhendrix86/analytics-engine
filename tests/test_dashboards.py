"""dashboards.py doesn't touch the database yet - every endpoint returns a
hardcoded/echoed response, independent of app/models/dashboard.py's real
Dashboard/Widget tables (covered separately in tests/test_models.py)."""


async def test_list_dashboards(client):
    r = await client.get("/dashboards/")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == len(body["dashboards"])


async def test_create_dashboard_returns_submitted_fields(client):
    r = await client.post("/dashboards/", json={"name": "Revenue Overview", "description": "Top-line metrics"})
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Revenue Overview"
    assert body["description"] == "Top-line metrics"


async def test_create_dashboard_requires_name(client):
    r = await client.post("/dashboards/", json={})
    assert r.status_code == 422


async def test_get_dashboard(client):
    r = await client.get("/dashboards/dashboard-1")
    assert r.status_code == 200
    assert r.json()["id"] == "dashboard-1"
