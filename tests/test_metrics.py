"""metrics.py is now real: /custom persists a real observation, /real-time and /historical read/aggregate real rows."""


async def _record_metric(client, **overrides):
    payload = {"name": "mrr", "metric_type": "revenue", "value": 25000, "unit": "USD"}
    payload.update(overrides)
    r = await client.post("/metrics/custom", json=payload)
    assert r.status_code == 200
    return r.json()


async def test_create_custom_metric_persists_a_real_row(client):
    body = await _record_metric(client)
    assert body["name"] == "mrr"
    assert body["value"] == 25000
    assert body["previous_value"] is None
    assert body["id"]  # a real generated UUID, not "metric_123"


async def test_create_custom_metric_requires_declared_fields(client):
    r = await client.post("/metrics/custom", json={"name": "x"})
    assert r.status_code == 422


async def test_second_observation_computes_real_previous_value_and_change(client):
    await _record_metric(client, value=25000)
    second = await _record_metric(client, value=27500)

    assert second["previous_value"] == 25000
    assert second["change_pct"] == 10.0


async def test_metric_allows_repeated_names_real_time_series(client):
    await _record_metric(client, value=100)
    r = await _record_metric(client, value=200)
    assert r["value"] == 200  # second observation succeeded - would 500 if name were still globally unique


async def test_real_time_metrics_reflects_latest_observation_per_name(client):
    await _record_metric(client, name="mrr", value=25000)
    await _record_metric(client, name="mrr", value=27500)
    await _record_metric(client, name="active_users", value=1500, metric_type="user")

    r = await client.get("/metrics/real-time")
    assert r.status_code == 200
    body = r.json()
    assert body["metrics"]["mrr"]["value"] == 27500
    assert body["metrics"]["active_users"]["value"] == 1500


async def test_real_time_metrics_with_nothing_recorded_is_honestly_empty(client):
    r = await client.get("/metrics/real-time")
    assert r.status_code == 200
    assert r.json()["metrics"] == {}


async def test_historical_metrics_filters_by_name_for_real(client):
    await _record_metric(client, name="mrr", value=25000)
    await _record_metric(client, name="active_users", value=1500, metric_type="user")

    r = await client.get("/metrics/historical", params={"metric_name": "mrr"})
    body = r.json()
    assert len(body["data"]) == 1
    assert body["data"][0]["name"] == "mrr"
