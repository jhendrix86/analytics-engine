"""
Analytics Engine - Main Application
Business intelligence and analytics system for the Autonomous Company OS
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
from datetime import datetime
import os

from app.config import settings
from app.database import init_db
from app.routers import metrics, dashboards, reports, predictions, kpi


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Analytics Engine...")
    
    # Initialize database
    await init_db()
    
    logger.info("Analytics Engine started successfully")
    yield
    
    logger.info("Shutting down Analytics Engine...")


# Create FastAPI application
app = FastAPI(
    title="Analytics Engine",
    description="Business intelligence and analytics system for the Autonomous Company OS",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
app.include_router(dashboards.router, prefix="/dashboards", tags=["dashboards"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
app.include_router(kpi.router, prefix="/kpi", tags=["kpi"])


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Analytics Engine",
        "version": "1.0.0",
        "status": "operational",
        "description": "Business intelligence and analytics system",
        "features": [
            "Data aggregation",
            "Real-time metrics",
            "Dashboard creation",
            "Predictive analytics",
            "Anomaly detection",
            "Custom reports",
            "Data visualization",
            "KPI tracking"
        ],
        "endpoints": {
            "metrics": "/metrics",
            "dashboards": "/dashboards",
            "reports": "/reports",
            "predictions": "/predictions",
            "kpi": "/kpi"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check performed")
    return {
        "status": "healthy",
        "service": "analytics-engine",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8042,
        reload=True
    )
