from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from agents import AgentOutputSchemaBase
import json

intent_schema = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": ["find_listings", "price_forecast", "legal_verification", 
                    "builder_reputation", "compare_locations", "check_freshness"]
        },
        "slots": {
            "type": "object",
            "properties": {
                "property_type": {"type": "string"},
                "max_price_inr": {"type": "integer"},
                "location": {"type": "string"},
                "radius_km": {"type": "number"},
                "rera_status": {"type": "string"},
                "goal": {"type": "string"},
                "near": {"type": "string"},
                "preferences": {"type": "array", "items": {"type": "string"}},
                "configuration": {"type": "string"},
                "builder": {"type": "string"},
                "time_horizon_years": {"type": "integer"}
            },
            "additionalProperties": True
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0
        },
        "model_version": {"type": "string"}
    },
    "required": ["intent", "slots", "confidence", "model_version"]
}

class IntentClassificationOutputSchema(AgentOutputSchemaBase):
    """A demonstration of a intent classsification output schema."""

    def is_plain_text(self) -> bool:
        return False

    def name(self) -> str:
        return "IntentClassificationOutputSchema"

    def json_schema(self) -> dict[str, Any]:
        return intent_schema

    def is_strict_json_schema(self) -> bool:
        return False

    def validate_json(self, json_str: str) -> Any:
        try:
            json_obj = json.loads(json_str)
            
            # Validate the response has required fields
            if "intent" not in json_obj:
                raise ValueError("Missing 'intent' field")
            if "slots" not in json_obj:
                raise ValueError("Missing 'slots' field")
            if "confidence" not in json_obj:
                raise ValueError("Missing 'confidence' field")
            if "model_version" not in json_obj:
                json_obj["model_version"] = "intent-clf-v1.0"  # Default if missing
                
            # Basic validation
            if not isinstance(json_obj["slots"], dict):
                raise ValueError("'slots' must be an object")
            if not (0 <= float(json_obj["confidence"]) <= 1.0):
                raise ValueError("'confidence' must be between 0.0 and 1.0")
                
            # Return the validated object
            return json_obj
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON string")