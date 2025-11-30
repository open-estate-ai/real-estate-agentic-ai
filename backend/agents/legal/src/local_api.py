"""
Legal Agent - FastAPI application.

This agent receives user queries, creates a plan of agent tasks,
and stores the plan in the database for execution by downstream agents.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator

from database import get_db_session, init_db
from sqlalchemy import text


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    print("👋 Shutting down Legal Agent")


app = FastAPI(
    title="Legal Agent",
    description="",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Legal-agent",
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
        "service": "Legal-agent",
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/legal-agent")
async def plan_query(request: dict):
    """Create an execution plan for a user query."""
    print(f"📥 Received request payload: {request}")
    return {"status": "received"}
