from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from agents import AgentOutputSchemaBase
import json


class ListingCandidate(BaseModel):
    """Individual property listing candidate"""
    id: str
    title: str
    location: str
    price_inr: int
    source: str
    rera_status: str
    builder_name: str


class SearchListingsResult(BaseModel):
    """Search listings result structure"""
    candidates: List[ListingCandidate]
    total_found: int
    search_params: Dict[str, Any]


search_listings_schema = {
    "type": "object",
    "properties": {
        "candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "location": {"type": "string"},
                    "price_inr": {"type": "integer"},
                    "source": {"type": "string"},
                    "rera_status": {"type": "string"},
                    "builder_name": {"type": "string"}
                },
                "required": ["id", "title", "location", "price_inr", "source", "rera_status", "builder_name"]
            }
        },
        "total_found": {"type": "integer"},
        "search_params": {"type": "object"}
    },
    "required": ["candidates", "total_found", "search_params"]
}


class SearchListingsOutputSchema(AgentOutputSchemaBase):
    """Search listings output schema for agents"""

    def is_plain_text(self) -> bool:
        return False

    def name(self) -> str:
        return "SearchListingsOutputSchema"

    def json_schema(self) -> dict[str, Any]:
        return search_listings_schema

    def is_strict_json_schema(self) -> bool:
        return False

    def validate_json(self, json_str: str) -> Any:
        try:
            json_obj = json.loads(json_str)
            
            # Validate required fields
            if "candidates" not in json_obj:
                raise ValueError("Missing 'candidates' field")
            if "total_found" not in json_obj:
                raise ValueError("Missing 'total_found' field")
            if "search_params" not in json_obj:
                raise ValueError("Missing 'search_params' field")
                
            # Basic validation
            if not isinstance(json_obj["candidates"], list):
                raise ValueError("'candidates' must be an array")
            if not isinstance(json_obj["total_found"], int):
                raise ValueError("'total_found' must be an integer")
                
            return json_obj
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON string")