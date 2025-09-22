import logging
from a2a.server.agent_execution import RequestContext
from agents import Agent, Runner, trace, function_tool
from orchestrator.models.intent import IntentClassificationOutputSchema
import json
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__) 


class OrchestratorAgent:

    
    async def classify_intent(self, user_text: str) -> str:
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
        # user_prompt = f"User query: {user_text}"
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




    async def invoke(self, context: RequestContext) -> str:
          
        classify_intent_result = await self.classify_intent(context.get_user_input())
        logger.info("Classify Intent Result: %s", classify_intent_result)
        return json.dumps(classify_intent_result, indent=2)
    