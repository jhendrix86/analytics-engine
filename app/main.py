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
from app.middleware.tenant import tenant_middleware


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
    lifespan=lifespan,
    # SECURITY_REVIEW.md finding: /docs, /redoc, /openapi.json were reachable
    # unauthenticated on every engine (dynamic-pentest-confirmed) - a full
    # interactive API browser plus every unauth write path. Disabled unless
    # DEBUG=true.
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# Configure CORS — see SECURITY_REVIEW.md finding #1: no wildcard with
# credentials; allowed origins come from the ALLOWED_ORIGINS env var.
def _cors_allowed_origins() -> list:
    # SECURITY_REVIEW.md #1 — no wildcard with credentials. Set
    # ALLOWED_ORIGINS (comma-separated) when a browser client exists.
    import os
    return [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tenant middleware for multi-tenancy support
app.middleware("http")(tenant_middleware)

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
