"""Planner module for orchestrator.

This module contains clean, human-readable deterministic planning logic that
builds a directed acyclic graph (DAG) of agent tasks based on a classified
intent and extracted slots.

Design goals:
- Deterministic (no LLM flakiness) while we iterate on agent ecosystem.
- Extensible: add/remove task builders without touching core flow.
- Transparent: each step has an explicit purpose + prompt instructions.

Public entrypoint: DeterministicPlanner.build_plan(...)
Returns PlannerOutput(dag=[DAGTask, ...], planner_meta={...}).
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import json

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

class DAGTask(BaseModel):
    """Represents a single unit of work executed by a downstream agent.

    Fields:
        task_id: Stable unique id within the plan (snake_case recommended)
        task_type: Logical agent type identifier (e.g., 'search_listings')
        payload_template: Dict template; values may include Jinja-like placeholders
        depends_on: List of task_ids this task waits on
        timeout_ms: Soft timeout guidance for execution layer
        parallel_for: Optional name of list in upstream output enabling fan-out
        agent_prompt: Natural language instructions tailored to this task
    """
    task_id: str
    task_type: str
    payload_template: Dict[str, Any]
    depends_on: List[str] = Field(default_factory=list)
    timeout_ms: int = 5000
    parallel_for: Optional[str] = None
    agent_prompt: Optional[str] = None

class PlannerOutput(BaseModel):
    """Container for planner results."""
    dag: List[DAGTask]
    planner_meta: Dict[str, Any]

# ---------------------------------------------------------------------------
# Deterministic Planner
# ---------------------------------------------------------------------------

class DeterministicPlanner:
    """Rule-based planner that converts (intent, slots) into a DAG.

    This avoids reliance on an LLM for structural planning while we stabilize
    core agents. You can later introduce an LLM layer that proposes a plan
    which is validated and possibly repaired by this deterministic backbone.
    """

    VERSION = "planner-v2.0.0"
    STRATEGY = "deterministic-rule-based"

    def __init__(self, *, enable_summary: bool = True) -> None:
        self.enable_summary = enable_summary

    # ----------------------------- Prompt Builders -------------------------
    def _prompt_search(self, slots: Dict[str, Any]) -> str:
        return (
            "Search for real estate listings matching the user's criteria.\n"
            f"Criteria (raw slots): {json.dumps(slots, ensure_ascii=False)}\n"
            "Map slots to provider query params. Return up to 25 high-quality candidates with fields: id, title, location, price_inr, source, rera_status, builder_name.\n"
            "If budget missing, still retrieve representative spectrum. If location vague (e.g., 'metro'), interpret as near transit hubs."
        )

    def _prompt_legal(self) -> str:
        return (
            "Perform regulatory & compliance (legal_check) screening over candidate listings.\n"
            "Input listing_ids come from previous search task.\n"
            "Check: RERA registration, land title clarity, litigation flags, builder reputation signals, embargo / restricted zones.\n"
            "Output JSON per listing id with fields: listing_id, rera_status, legal_risk_level (LOW|MEDIUM|HIGH), issues (array of short codes)."
        )

    def _prompt_valuation(self) -> str:
        return (
            "Run valuation_analysis for each candidate listing to estimate fair price range.\n"
            "Use comparable sales, locality average PSF, builder track record.\n"
            "Output: listing_id, estimated_value_inr, low_inr, high_inr, valuation_confidence (0-1), methodology_notes (short)."
        )

    def _prompt_verification(self) -> str:
        return (
            "Execute verification_scan to detect anomalies or fraud patterns in candidate listings.\n"
            "Heuristics: price too low relative to comps, duplicate contact numbers, suspicious recently created builder entity.\n"
            "Output: listing_id, anomaly_score (0-1), flags (array of short strings)."
        )

    def _prompt_summary(self, task_ids: List[str], intent: str, slots: Dict[str, Any]) -> str:
        return (
            "Synthesize results across enrichment tasks into a concise user-facing summary.\n"
            f"Aggregate from tasks: {', '.join(task_ids)}.\n"
            "Highlight top 5 listings (balanced by legal risk LOW & high valuation confidence).\n"
            "Include any HIGH risk warnings and valuation ranges. Provide next recommended user actions."
        )

    # ------------------------------ Utilities -----------------------------
    @staticmethod
    def _norm(slots: Dict[str, Any], name: str, default: str = "") -> str:
        v = slots.get(name)
        return str(v) if v is not None else default

    # ------------------------------ Main Logic ----------------------------
    def build_plan(self, request_id: str, intent: str, slots: Dict[str, Any]) -> PlannerOutput:
        tasks: List[DAGTask] = []

        include_search = intent in {"find_listings", "legal_verification", "compare_locations"}
        include_legal = intent in {"find_listings", "legal_verification"}
        include_valuation = intent in {"find_listings", "price_forecast", "compare_locations"}
        include_verification = intent in {"find_listings", "legal_verification", "compare_locations"}

        # search_listings
        if include_search:
            tasks.append(DAGTask(
                task_id="t1_search",
                task_type="search_listings",
                payload_template={
                    "property_type": self._norm(slots, "property_type"),
                    "max_price_inr": slots.get("max_price_inr"),
                    "near": self._norm(slots, "near", self._norm(slots, "location")),
                    "raw_slots": slots
                },
                depends_on=[],
                timeout_ms=7000,
                agent_prompt=self._prompt_search(slots)
            ))

        # legal_check
        if include_legal and include_search:
            tasks.append(DAGTask(
                task_id="t2_legal",
                task_type="legal_check",
                payload_template={"listing_ids": "{{t1_search.candidates.ids}}"},
                depends_on=["t1_search"],
                timeout_ms=8000,
                parallel_for="candidates",
                agent_prompt=self._prompt_legal()
            ))
        elif include_legal:
            tasks.append(DAGTask(
                task_id="t1_legal",
                task_type="legal_check",
                payload_template={"listing_ids": slots.get("listing_ids", [])},
                depends_on=[],
                timeout_ms=6000,
                agent_prompt=self._prompt_legal()
            ))

        # valuation_analysis
        if include_valuation and include_search:
            tasks.append(DAGTask(
                task_id="t3_valuation" if any(t.task_id == "t2_legal" for t in tasks) else "t2_valuation",
                task_type="valuation_analysis",
                payload_template={
                    "listing_ids": "{{t1_search.candidates.ids}}",
                    "property_type": self._norm(slots, "property_type"),
                    "max_price_inr": slots.get("max_price_inr")
                },
                depends_on=["t1_search"],
                timeout_ms=7500,
                parallel_for="candidates",
                agent_prompt=self._prompt_valuation()
            ))
        elif include_valuation:
            tasks.append(DAGTask(
                task_id="t1_valuation",
                task_type="valuation_analysis",
                payload_template={
                    "listing_ids": slots.get("listing_ids", []),
                    "property_type": self._norm(slots, "property_type"),
                    "max_price_inr": slots.get("max_price_inr")
                },
                depends_on=[],
                timeout_ms=6500,
                agent_prompt=self._prompt_valuation()
            ))

        # verification_scan
        if include_verification and include_search:
            tasks.append(DAGTask(
                task_id="t4_verification" if any(t.task_type == "valuation_analysis" for t in tasks) else (
                    "t3_verification" if any(t.task_type == "legal_check" for t in tasks) else "t2_verification"),
                task_type="verification_scan",
                payload_template={"listing_ids": "{{t1_search.candidates.ids}}"},
                depends_on=["t1_search"],
                timeout_ms=6000,
                parallel_for="candidates",
                agent_prompt=self._prompt_verification()
            ))
        elif include_verification:
            tasks.append(DAGTask(
                task_id="t1_verification",
                task_type="verification_scan",
                payload_template={"listing_ids": slots.get("listing_ids", [])},
                depends_on=[],
                timeout_ms=5000,
                agent_prompt=self._prompt_verification()
            ))

        # summarization
        if self.enable_summary and tasks:
            upstream = [t.task_id for t in tasks if t.task_type != "summarization"]
            tasks.append(DAGTask(
                task_id="t_final_summary",
                task_type="summarization",
                payload_template={
                    "upstream_tasks": upstream,
                    "original_intent": intent,
                    "original_slots": slots
                },
                depends_on=upstream,
                timeout_ms=4000,
                agent_prompt=self._prompt_summary(upstream, intent, slots)
            ))

        # Fallback for empty plan
        if not tasks:
            tasks.append(DAGTask(
                task_id="t1_generic",
                task_type="generic_handler",
                payload_template={"original_slots": slots},
                depends_on=[],
                timeout_ms=3000,
                agent_prompt=(
                    "Handle the user request generically; intent was not recognized with confidence. "
                    "Extract any actionable real-estate signals."
                )
            ))

        meta = {
            "version": self.VERSION,
            "strategy": self.STRATEGY,
            "request_id": request_id,
            "intent": intent
        }
        return PlannerOutput(dag=tasks, planner_meta=meta)