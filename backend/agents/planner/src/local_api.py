"""
Planner Agent - FastAPI application.

This agent receives user queries, creates a plan of agent tasks,
and stores the plan in the database for execution by downstream agents.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from database import get_db_session, init_db

from .services import PlannerService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    # print("🚀 Initializing Planner Agent...")
    # init_db()
    # print("✅ Database initialized")
    yield
    print("👋 Shutting down Planner Agent")


app = FastAPI(
    title="Planner Agent",
    description="Creates execution plans for user queries",
    version="0.1.0",
    lifespan=lifespan,
)


class PlanRequest(BaseModel):
    """Request model for planning."""
    job_id: str
    query: str
    user_id: str | None = None
    context: dict | None = None


class PlanResponse(BaseModel):
    """Response model for planning."""
    job_id: str
    status: str
    plan: dict | None = None
    error: str | None = None


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "planner-agent",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    # Test database connection
    try:
        with get_db_session() as session:
            session.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "service": "planner-agent",
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/user-query", response_model=PlanResponse)
async def plan_query(request: PlanRequest):
    """Create an execution plan for a user query."""
    try:
        result = await PlannerService.create_plan_for_query(
            job_id=request.job_id,
            query=request.query,
            user_id=request.user_id,
            context=request.context or {},
        )

        return PlanResponse(
            job_id=result["job_id"],
            status="completed",
            plan=result["plan"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @app.get("/jobs/{job_id}")
# async def get_job_status(job_id: str):
#     """Get status of a planning job."""
#     job = PlannerService.get_job_details(job_id)

#     if not job:
#         raise HTTPException(status_code=404, detail="Job not found")

#     return job


# @app.get("/jobs/{job_id}/children")
# async def get_child_jobs(job_id: str):
#     """Get all child jobs for a planning job."""
#     children = PlannerService.get_job_children(job_id)

#     return {
#         "parent_job_id": job_id,
#         "child_count": len(children),
#         "children": children,
#     }
