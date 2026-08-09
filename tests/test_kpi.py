"""kpi.py's routes don't touch the database yet - see
tests/test_dashboards.py's module docstring for the same pattern. The real
KPI/KPIGoal models are covered separately in tests/test_models.py."""


async def test_list_kpis(client):
    r = await client.get("/kpi/")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == len(body["kpis"])


async def test_create_kpi_returns_submitted_fields(client):
    r = await client.post("/kpi/", json={"name": "Signup Conversion", "metric": "conversion_rate", "target": 0.05})
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Signup Conversion"
    assert body["target"] == 0.05


async def test_create_kpi_requires_declared_fields(client):
    r = await client.post("/kpi/", json={"name": "x"})
    assert r.status_code == 422


async def test_get_kpi(client):
    r = await client.get("/kpi/kpi-1")
    assert r.status_code == 200
    assert r.json()["id"] == "kpi-1"
