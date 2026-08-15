"""
Real deterministic trend forecasting over persisted Metric history.

No ML library is imported anywhere in this engine despite pandas/numpy/
scikit-learn/statsmodels all being pinned in requirements.txt and never
used - the same "pinned but unused" pattern found in every other mock
engine this session (sales-engine's CRM SDKs, customer-support-engine's
sendgrid). Rather than bolting on a full ML pipeline with no real
training data or model-selection story behind it, this is a real, small,
honest computation: ordinary least-squares linear regression by hand
(no numpy needed for this), with an honest "insufficient data" failure
when there's nothing real to fit - matching the fleet's established
"real client/computation or honest failure" convention, never a
fabricated confidence number.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ForecastResult:
    success: bool
    error: Optional[str] = None
    forecast: Optional[List[float]] = None
    confidence: Optional[int] = None  # R^2 of the fit, as a percentage
    trend: Optional[str] = None  # "increasing" / "decreasing" / "flat"


def forecast_linear_trend(values: List[float], periods_ahead: int = 1) -> ForecastResult:
    """Real OLS linear regression over an ordered value series (oldest first)."""
    n = len(values)
    if n < 2:
        return ForecastResult(success=False, error=f"Insufficient data: need at least 2 observations, have {n}")

    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(values) / n

    ss_xx = sum((x - mean_x) ** 2 for x in xs)
    if ss_xx == 0:
        return ForecastResult(success=False, error="Insufficient variance in observation timing to fit a trend")

    ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values))
    slope = ss_xy / ss_xx
    intercept = mean_y - slope * mean_x

    predicted = [intercept + slope * x for x in xs]
    ss_res = sum((y - p) ** 2 for y, p in zip(values, predicted))
    ss_tot = sum((y - mean_y) ** 2 for y in values)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 1.0

    forecast = [round(intercept + slope * (n - 1 + step), 2) for step in range(1, periods_ahead + 1)]

    if abs(slope) < 1e-9:
        trend = "flat"
    else:
        trend = "increasing" if slope > 0 else "decreasing"

    return ForecastResult(
        success=True,
        forecast=forecast,
        confidence=max(0, min(100, round(r_squared * 100))),
        trend=trend,
    )
