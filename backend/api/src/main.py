"""FastAPI application for local development."""

import logging
import os
import uuid

from fastapi import FastAPI, HTTPException
from mangum import Mangum
from database import get_db_session, init_db

from .clients import PlannerClient
from .services import ApiService

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

ENV = os.getenv("ENV", "local")
PLANNER_AGENT_URL = os.getenv("PLANNER_AGENT_URL", "http://localhost:8080")

# Create FastAPI app with /api prefix
app = FastAPI(
    title="Backend API Service",
    description="Analyzes user queries and manages jobs",
    version="0.1.0",
    root_path="/api",  # Add this to handle /api prefix
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "backend-api-service",
        "status": "healthy",
        "env": ENV,
    }


@app.get("/health")
async def health():
    """Health check with database status."""
    db_status = ApiService.check_database_health()

    return {
        "service": "backend-api-service",
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "env": ENV,
    }


@app.post("/analyze")
async def analyze(query: str, user_id: str | None = None):
    """Analyze user query and create execution plan."""
    try:
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        logger.info(f"Analyzing query for job_id={job_id}")

        if ENV == "local":
            # Local: Make HTTP call to planner agent
            logger.info("Using local planner agent via HTTP")
            planner_client = PlannerClient(base_url=PLANNER_AGENT_URL)
            result = await planner_client.create_plan(
                job_id=job_id,
                query=query,
                user_id=user_id,
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


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a planning job."""
    job = ApiService.get_job_details(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@app.get("/jobs/{job_id}/children")
async def get_child_jobs(job_id: str):
    """Get all child jobs for a planning job."""
    children = ApiService.get_job_children(job_id)

    return {
        "parent_job_id": job_id,
        "child_count": len(children),
        "children": children,
    }

lambda_handler = Mangum(app)
