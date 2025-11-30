from dataclasses import dataclass


@dataclass
class PlannerContext:
    """Context for planner agent tools."""
    job_id: str
