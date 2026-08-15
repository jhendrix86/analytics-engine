"""reports.py is now real: /generate computes real aggregates from recorded Metric rows, never a fake output_url."""


async def _record_metric(client, **overrides):
    payload = {"name": "mrr", "metric_type": "revenue", "value": 25000, "unit": "USD"}
    payload.update(overrides)
    return (await client.post("/metrics/custom", json=payload)).json()


async def _create_report(client, **overrides):
    payload = {"name": "Q1 Revenue Report", "report_type": "revenue", "metric_names": ["mrr"]}
    payload.update(overrides)
    r = await client.post("/reports/", json=payload)
    assert r.status_code == 200
    return r.json()


async def test_create_report_persists_a_real_pending_row(client):
    body = await _create_report(client)
    assert body["name"] == "Q1 Revenue Report"
    assert body["status"] == "pending"
    assert body["data"] is None
    assert body["id"]  # a real generated UUID, not "report-1"


async def test_generate_report_with_no_matching_metrics_fails_honestly(client):
    report = await _create_report(client, metric_names=["nonexistent_metric"])

    r = await client.post(f"/reports/{report['id']}/generate")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "failed"
    assert "No metrics found" in body["error_message"]


async def test_generate_report_computes_real_aggregates(client):
    await _record_metric(client, name="mrr", value=25000)
    await _record_metric(client, name="mrr", value=27000)
    report = await _create_report(client, metric_names=["mrr"])

    r = await client.post(f"/reports/{report['id']}/generate")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "completed"
    assert body["data"]["mrr"]["count"] == 2
    assert body["data"]["mrr"]["latest"] == 27000
    assert body["data"]["mrr"]["avg"] == 26000.0


async def test_generate_unknown_report_is_a_real_404(client):
    r = await client.post("/reports/00000000-0000-0000-0000-000000000000/generate")
    assert r.status_code == 404


async def test_get_report_returns_the_real_row(client):
    report = await _create_report(client)
    r = await client.get(f"/reports/{report['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == report["id"]


async def test_get_unknown_report_is_a_real_404(client):
    r = await client.get("/reports/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_list_reports_reflects_real_created_rows(client):
    await _create_report(client, name="one")
    await _create_report(client, name="two")

    r = await client.get("/reports/")
    assert r.json()["total"] == 2
