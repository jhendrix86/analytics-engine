"""metrics.py is 100% mock - every endpoint documents "In production, this
would... For now, return a mock response" and never touches the database."""


async def test_get_real_time_metrics(client):
    r = await client.get("/metrics/real-time")
    assert r.status_code == 200
    body = r.json()
    assert "revenue" in body["metrics"]
    assert "mrr" in body["metrics"]


async def test_get_historical_metrics_defaults_to_30_day_window(client):
    r = await client.get("/metrics/historical")
    assert r.status_code == 200
    assert "period" in r.json()


async def test_get_historical_metrics_echoes_explicit_dates(client):
    r = await client.get("/metrics/historical", params={"start_date": "2026-01-01", "end_date": "2026-01-31"})
    assert r.status_code == 200
    assert r.json()["period"] == {"start_date": "2026-01-01", "end_date": "2026-01-31"}


async def test_create_custom_metric_returns_submitted_fields(client):
    r = await client.post("/metrics/custom", json={"name": "signups", "metric_type": "user", "value": 42})
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "signups"
    assert body["value"] == 42


async def test_create_custom_metric_requires_declared_fields(client):
    r = await client.post("/metrics/custom", json={"name": "x"})
    assert r.status_code == 422
