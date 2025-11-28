"""
FastAPI application for Backend API service.

Environment-based configuration:
- ENV=local: Uses local Docker PostgreSQL, local Planner Agent
- ENV=dev/stage/production: Uses AWS RDS, deployed Planner Agent
"""

import logging
import os
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from database import get_db_session, init_db

from .clients import PlannerClient
from .services import ApiService

# =============================================================================
# CONFIGURATION
# =============================================================================

# Environment detection (used by database connection)
ENV = os.getenv("ENV", "local")

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Agent endpoint
PLANNER_AGENT_URL = os.getenv("PLANNER_AGENT_URL", "http://localhost:8081")

logger.info(f"Starting Backend API in {ENV} environment")
logger.info(f"Database connection will use ENV={ENV} settings")

# Create FastAPI app with /api prefix
app = FastAPI(
    title="Backend API Service",
    description="Analyzes user queries and manages jobs",
    version="0.1.0"
)


@app.get("/api/")
async def root():
    """Root endpoint."""
    return {
        "service": "backend-api-service",
        "status": "healthy",
        "env": ENV,
    }


@app.get("/api/health")
async def health():
    """Health check with database status."""
    db_status = ApiService.check_database_health()

    return {
        "service": "backend-api-service",
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "env": ENV,
    }


class AnalyzeRequest(BaseModel):
    """Request model for analyze endpoint."""
    user_id: str | None = None
    request_payload: dict[str, Any]

    @validator('request_payload')
    def validate_request_payload(cls, v):
        if 'user_query' not in v:
            raise ValueError('request_payload must contain user_query')
        return v


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    """Analyze user query and create execution plan."""
    try:
        job_id = str(uuid.uuid4())  # Generate proper UUID
        user_query = request.request_payload.get('user_query')
        logger.info(f"Analyzing query for job_id={job_id}: {user_query}")

        if ENV == "local":
            # Local: Make HTTP call to planner agent
            logger.info("Using local planner agent via HTTP")
            planner_client = PlannerClient()
            result = await planner_client.create_plan(
                job_id=job_id,
                user_query=user_query,
                user_id=request.user_id,
            )

            return {
                "job_id": job_id,
                "message": "Query submitted for analysis",
            }

        else:
            # Production: Send to SQS
            logger.info("Using SQS for production")
            # TODO: Implement SQS message sending
            raise NotImplementedError("SQS integration not yet implemented")

    except Exception as e:
        logger.error(f"Error in analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a planning job."""
    job = ApiService.get_job_details(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job
