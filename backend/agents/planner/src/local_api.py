"""
Planner Agent - FastAPI application.

This agent receives user queries, creates a plan of agent tasks,
and stores the plan in the database for execution by downstream agents.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator

from database import get_db_session, init_db
from sqlalchemy import text

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
    user_id: str | None = None
    request_payload: dict

    @validator('request_payload')
    def validate_request_payload(cls, v):
        if not isinstance(v, dict):
            raise ValueError('request_payload must be a dictionary')
        if 'user_query' not in v:
            raise ValueError('request_payload must contain user_query')
        if not v.get('user_query', '').strip():
            raise ValueError('user_query cannot be empty')
        return v

    def get_user_query(self) -> str:
        """Extract user query from request payload."""
        return self.request_payload.get('user_query', '').strip()


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
            session.execute(text("SELECT 1"))
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
        user_query = request.get_user_query()

        print(f"🔍 Processing planning request:")
        print(f"  - Job ID: {request.job_id}")
        print(f"  - User ID: {request.user_id}")
        print(f"  - Query: {user_query}")

        result = await PlannerService.create_plan_for_query(
            job_id=request.job_id,
            user_query=user_query,
            user_id=request.user_id,
        )

        print(f"✅ Planning completed for job {request.job_id}")
        print("✅ Plan execution started.")

        await PlannerService.create_execute_plan(
            job_id=request.job_id
        )

        print(f"✅ Plan execution completed for job {request.job_id}")
        print(f"✅ Planning completed for job {request.job_id}")

        return PlanResponse(
            job_id=result["job_id"],
            status="completed",
            plan=result["plan"],
        )

    except ValueError as e:
        print(f"❌ Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Planning error for job {request.job_id}: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail=f"Planning failed: {str(e)}")


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
