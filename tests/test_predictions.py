"""predictions.py is now real: FORECAST predictions compute a real linear-trend fit over recorded Metric history."""


async def _record_metric(client, value, **overrides):
    payload = {"name": "mrr", "metric_type": "revenue", "value": value}
    payload.update(overrides)
    return (await client.post("/metrics/custom", json=payload)).json()


async def test_create_forecast_without_enough_history_fails_honestly(client):
    await _record_metric(client, 100)  # only 1 observation - can't fit a trend

    r = await client.post("/predictions/", json={"name": "MRR forecast", "metric_name": "mrr"})
    assert r.status_code == 422
    assert "Insufficient data" in r.json()["detail"]


async def test_create_forecast_computes_a_real_trend(client):
    for value in [100, 200, 300, 400]:
        await _record_metric(client, value)

    r = await client.post("/predictions/", json={"name": "MRR forecast", "metric_name": "mrr", "periods_ahead": 2})
    assert r.status_code == 200
    body = r.json()
    assert body["prediction_type"] == "forecast"
    assert body["prediction"]["trend"] == "increasing"
    assert body["prediction"]["forecast"] == [500.0, 600.0]
    assert body["confidence"] == 100  # a perfectly linear series fits with R^2 = 1
    assert body["id"]  # a real generated UUID, not "prediction-1"


async def test_create_forecast_requires_metric_name(client):
    r = await client.post("/predictions/", json={"name": "x"})
    assert r.status_code == 400


async def test_create_non_forecast_prediction_is_rejected_honestly(client):
    r = await client.post("/predictions/", json={"name": "x", "prediction_type": "anomaly", "metric_name": "mrr"})
    assert r.status_code == 400
    assert "no real model" in r.json()["detail"]


async def test_get_unknown_prediction_is_a_real_404(client):
    r = await client.get("/predictions/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_list_predictions_reflects_real_created_rows(client):
    for value in [100, 200]:
        await _record_metric(client, value)
    await client.post("/predictions/", json={"name": "MRR forecast", "metric_name": "mrr"})

    r = await client.get("/predictions/")
    assert r.json()["total"] == 1
