import logging
import json
import uuid
from typing import Dict, Any

from a2a.server.agent_execution import RequestContext
from agents import Agent, Runner, trace

from orchestrator.models.intent import IntentClassificationOutputSchema
from orchestrator.planner import DeterministicPlanner, PlannerOutput, DAGTask

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__) 


"""Orchestrator Agent integrates intent classification + deterministic planning."""


class OrchestratorAgent:

    async def classify_intent(self, user_text: str) -> dict:
        """
        Use OpenAI 'responses' with JSON Schema to extract intent + slots.
        Returns dict with keys: intent, slots, confidence, model_version, raw_resp
        """
        system_prompt = (
            "You are OrchestratorAgent — Intent Extractor for real estate queries. Your job is to extract structured information from user queries about properties."
            "\n\n"
            "Extract the following fields:"
            "\n- intent: The primary user intention (find_listings, price_forecast, legal_verification, builder_reputation, compare_locations, check_freshness)"
            "\n- slots: Key parameters like property_type, max_price_inr, location, radius_km, rera_status, goal, etc."
            "\n- confidence: A float between 0.0-1.0 indicating your confidence in this classification"
            "\n- model_version: Always set to 'intent-clf-v1.0'"
            "\n\n"
            "Example user query: 'Find plots under 80 lakh near metro with RERA approval'"
            "\nExample response: {'intent': 'find_listings', 'slots': {'property_type': 'plot', 'max_price_inr': 8000000, 'near': 'metro', 'rera_status': 'approved'}, 'confidence': 0.95, 'model_version': 'intent-clf-v1.0'}"
            "\n\n"
            "Return ONLY a valid JSON object matching the IntentClassification schema."
        )
        try:
            intent_clf_v1 = Agent(
                name="Intent Classifier Agent",
                instructions=system_prompt,
                output_type=IntentClassificationOutputSchema(),
                model="gpt-4o-mini")
            
            with trace("Intent Classification"):
                result = await Runner.run(intent_clf_v1, user_text)
            return result.final_output
        except Exception as e:
            print(f"Error in classify_intent: {e}")
            # Return a fallback result
            return {
                "intent": "unknown",
                "slots": {},
                "confidence": 0.0,
                "model_version": "intent-clf-v1.0"
            }

    async def plan_workflow(self, request_id: str, intent_result: dict) -> PlannerOutput:
        """Delegate to DeterministicPlanner (can later add policy / feature flags)."""
        intent = (intent_result or {}).get("intent", "unknown")
        slots: Dict[str, Any] = (intent_result or {}).get("slots", {}) or {}
        planner = DeterministicPlanner(enable_summary=True)
        return planner.build_plan(request_id, intent, slots)

    async def invoke(self, context: RequestContext) -> str:
        # Step 1: classify intent
        classify_intent_result = await self.classify_intent(context.get_user_input())
        logger.info("Intent Classification: %s", classify_intent_result)

        # Step 2: plan workflow using classification
        request_id = getattr(context, "request_id", str(uuid.uuid4()))
        planner_output = await self.plan_workflow(request_id, classify_intent_result)
        logger.info("Planner Output: %s", planner_output.model_dump())

        response = {
            "request_id": request_id,
            "intent": classify_intent_result.get("intent"),
            "slots": classify_intent_result.get("slots", {}),
            "confidence": classify_intent_result.get("confidence"),
            "model_version": classify_intent_result.get("model_version"),
            "dag": [t.model_dump() for t in planner_output.dag],
            "planner_meta": planner_output.planner_meta
        }
        return json.dumps(response, indent=2)
    