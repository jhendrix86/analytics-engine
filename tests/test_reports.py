"""reports.py doesn't touch the database yet - see tests/test_dashboards.py's
module docstring for the same pattern."""


async def test_list_reports(client):
    r = await client.get("/reports/")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == len(body["reports"])


async def test_create_report_returns_submitted_fields(client):
    r = await client.post("/reports/", json={"name": "Q1 Revenue", "description": "Quarterly summary"})
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Q1 Revenue"


async def test_create_report_requires_name(client):
    r = await client.post("/reports/", json={})
    assert r.status_code == 422


async def test_get_report(client):
    r = await client.get("/reports/report-1")
    assert r.status_code == 200
    assert r.json()["id"] == "report-1"
