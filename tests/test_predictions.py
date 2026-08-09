"""predictions.py doesn't touch the database yet - see
tests/test_dashboards.py's module docstring for the same pattern."""


async def test_list_predictions(client):
    r = await client.get("/predictions/")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == len(body["predictions"])


async def test_create_prediction_returns_submitted_fields(client):
    r = await client.post("/predictions/", json={"name": "Q2 churn forecast", "model": "arima"})
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Q2 churn forecast"
    assert body["status"] == "pending"


async def test_create_prediction_requires_declared_fields(client):
    r = await client.post("/predictions/", json={"name": "x"})
    assert r.status_code == 422


async def test_get_prediction(client):
    r = await client.get("/predictions/prediction-1")
    assert r.status_code == 200
    assert r.json()["id"] == "prediction-1"
