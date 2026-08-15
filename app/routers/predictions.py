"""
Predictions router - real DB-backed CRUD, and creating a FORECAST
prediction actually computes a real linear-trend forecast
(app/services/forecast.py) over persisted Metric history, with an
honest failure when there isn't enough real data to fit - never a
fabricated confidence/result the way the old mock did.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.metric import Metric
from app.models.prediction import Prediction, PredictionType
from app.models.tenant_base import apply_tenant_context
from app.services.forecast import forecast_linear_trend

router = APIRouter()


class CreatePredictionRequest(BaseModel):
    """Request to create a prediction. For FORECAST, metric_name is required -
    the forecast is computed for real from that metric's own recorded history."""
    name: str
    prediction_type: PredictionType = PredictionType.FORECAST
    metric_name: Optional[str] = None
    periods_ahead: int = 1
    model_name: str = "linear-trend"


def _serialize(prediction: Prediction) -> dict:
    return {
        "id": str(prediction.id),
        "name": prediction.name,
        "prediction_type": prediction.prediction_type.value,
        "model_name": prediction.model_name,
        "model_version": prediction.model_version,
        "input_data": prediction.input_data,
        "prediction": prediction.prediction,
        "confidence": prediction.confidence,
        "predicted_at": prediction.predicted_at.isoformat(),
    }


async def _get_prediction_or_404(db: AsyncSession, prediction_id: str) -> Prediction:
    try:
        prediction_uuid = uuid.UUID(prediction_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Prediction '{prediction_id}' not found")

    prediction = await db.get(Prediction, prediction_uuid)
    if prediction is None:
        raise HTTPException(status_code=404, detail=f"Prediction '{prediction_id}' not found")
    return prediction


@router.get("/")
async def list_predictions(db: AsyncSession = Depends(get_db)):
    """List all predictions, real query"""
    result = await db.execute(select(Prediction).order_by(Prediction.predicted_at.desc()))
    predictions = result.scalars().all()
    return {"predictions": [_serialize(p) for p in predictions], "total": len(predictions)}


@router.post("/")
async def create_prediction(request: CreatePredictionRequest, db: AsyncSession = Depends(get_db)):
    """Create a prediction - FORECAST types are computed for real from Metric history"""
    try:
        logger.info(f"Creating prediction: {request.name} ({request.prediction_type.value})")

        if request.prediction_type != PredictionType.FORECAST:
            raise HTTPException(
                status_code=400,
                detail=f"Only FORECAST predictions are computed today; {request.prediction_type.value} has no real model behind it yet",
            )
        if not request.metric_name:
            raise HTTPException(status_code=400, detail="metric_name is required for a FORECAST prediction")

        result = await db.execute(
            select(Metric.value).where(Metric.name == request.metric_name).order_by(Metric.timestamp)
        )
        values = [row[0] for row in result.all()]

        forecast = forecast_linear_trend([float(v) for v in values], request.periods_ahead)

        if not forecast.success:
            raise HTTPException(status_code=422, detail=forecast.error)

        prediction = Prediction(
            name=request.name,
            prediction_type=request.prediction_type,
            model_name=request.model_name,
            input_data={"metric_name": request.metric_name, "observations": values, "periods_ahead": request.periods_ahead},
            prediction={"forecast": forecast.forecast, "trend": forecast.trend},
            confidence=forecast.confidence,
        )
        apply_tenant_context(prediction)

        db.add(prediction)
        await db.commit()
        await db.refresh(prediction)

        logger.info(f"Prediction created: {prediction.id}")
        return _serialize(prediction)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{prediction_id}")
async def get_prediction(prediction_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific prediction"""
    try:
        prediction = await _get_prediction_or_404(db, prediction_id)
        return _serialize(prediction)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))
