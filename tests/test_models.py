"""
Real tests for the SQLAlchemy models - test_smoke.py only checked that they
import, not that the schema/relationships actually work.
"""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.metric import Metric, MetricType
from app.models.dashboard import Dashboard, Widget
from app.models.kpi import KPI, KPIGoal
from app.models.report import Report, ReportStatus
from app.models.prediction import Prediction, PredictionType


async def test_metric_allows_multiple_observations_with_the_same_name(db_session):
    """
    A global unique constraint on Metric.name used to make it impossible
    to ever record a second data point for the same metric - a real,
    blocking bug for a time-series table, fixed this session (removed,
    not just relaxed to per-tenant, since the same metric name legitimately
    repeats across many timestamps for a single tenant too).
    """
    db_session.add(Metric(name="mrr", metric_type=MetricType.REVENUE, value=25000, unit="USD"))
    db_session.add(Metric(name="mrr", metric_type=MetricType.REVENUE, value=26000, unit="USD"))
    await db_session.commit()

    result = await db_session.execute(select(Metric).where(Metric.name == "mrr"))
    assert len(result.scalars().all()) == 2


async def test_dashboard_widget_relationship_round_trips(db_session):
    dashboard = Dashboard(name="Revenue Overview", layout={"cols": 12})
    db_session.add(dashboard)
    await db_session.flush()

    widget = Widget(dashboard_id=dashboard.id, widget_type="chart", title="MRR Trend", config={"metric": "mrr"})
    db_session.add(widget)
    await db_session.commit()

    result = await db_session.execute(select(Dashboard).where(Dashboard.id == dashboard.id))
    fetched = result.scalar_one()
    await db_session.refresh(fetched, attribute_names=["widgets"])

    assert len(fetched.widgets) == 1
    assert fetched.widgets[0].title == "MRR Trend"
    assert fetched.widgets[0].dashboard.name == "Revenue Overview"


async def test_dashboard_delete_cascades_to_widgets(db_session):
    """Widget has cascade="all, delete-orphan" - verify it actually does."""
    dashboard = Dashboard(name="Temp Dashboard", layout={})
    db_session.add(dashboard)
    await db_session.flush()
    db_session.add(Widget(dashboard_id=dashboard.id, widget_type="table", title="Data", config={}))
    await db_session.commit()

    await db_session.delete(dashboard)
    await db_session.commit()

    result = await db_session.execute(select(Widget))
    assert result.scalars().all() == []


async def test_kpi_goal_relationship_round_trips(db_session):
    kpi = KPI(name="Signup Conversion", current_value=3, target_value=5)
    db_session.add(kpi)
    await db_session.flush()

    goal = KPIGoal(
        kpi_id=kpi.id, target_value=5, start_value=3,
        start_date=datetime.utcnow(), end_date=datetime.utcnow() + timedelta(days=30),
    )
    db_session.add(goal)
    await db_session.commit()

    result = await db_session.execute(select(KPI).where(KPI.id == kpi.id))
    fetched = result.scalar_one()
    await db_session.refresh(fetched, attribute_names=["goals"])

    assert len(fetched.goals) == 1
    assert fetched.goals[0].achieved is False


async def test_kpi_goal_requires_a_kpi(db_session):
    goal = KPIGoal(
        kpi_id=uuid.uuid4(), target_value=1, start_value=0,
        start_date=datetime.utcnow(), end_date=datetime.utcnow(),
    )
    db_session.add(goal)
    try:
        await db_session.commit()
        assert False, "expected an IntegrityError for a nonexistent kpi_id"
    except IntegrityError:
        await db_session.rollback()


async def test_report_default_status_is_pending(db_session):
    report = Report(name="Q1 Revenue Report", report_type="revenue", config={})
    db_session.add(report)
    await db_session.commit()
    await db_session.refresh(report)

    assert report.status == ReportStatus.PENDING
    assert report.output_format == "pdf"


async def test_prediction_persists_json_fields(db_session):
    prediction = Prediction(
        name="Q2 churn forecast", prediction_type=PredictionType.FORECAST,
        input_data={"history": [1, 2, 3]}, prediction={"churn_rate": 0.05}, confidence=82,
    )
    db_session.add(prediction)
    await db_session.commit()

    result = await db_session.execute(select(Prediction).where(Prediction.name == "Q2 churn forecast"))
    fetched = result.scalar_one()
    assert fetched.prediction == {"churn_rate": 0.05}
    assert fetched.prediction_type == PredictionType.FORECAST
