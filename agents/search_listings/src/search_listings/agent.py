import logging
import json
import uuid
from typing import Dict, Any

from a2a.server.agent_execution import RequestContext
from agents import Agent, Runner, trace

# We'll need a search listings specific output schema
from search_listings.models.search import SearchListingsOutputSchema

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger(__name__) 


"""SearchListingsAgent specializes in searching for real estate listings based on user criteria."""


class SearchListingsAgent:

    async def search_listings(self, search_payload: dict) -> dict:
        """
        Search for property listings based on provided criteria.
        Returns dict with keys: candidates, total_found, search_params
        """
        system_prompt = (
            "You are SearchListingsAgent — a specialized real estate search agent that finds property listings based on user criteria."
            "\n\n"
            "Your job is to:"
            "\n- Parse search criteria from the input payload (property_type, max_price_inr, location, near, rera_status, etc.)"
            "\n- Search and retrieve relevant real estate listings"
            "\n- Return structured results with high-quality candidates"
            "\n\n"
            "Input format: You'll receive a payload_template with search parameters like:"
            "\n{'property_type': 'plot', 'max_price_inr': 8000000, 'near': 'metro', 'location': 'Sonipat, Haryana', 'rera_status': 'approved'}"
            "\n\n"
            "Search guidelines:"
            "\n- If budget (max_price_inr) is missing, retrieve a representative spectrum of prices"
            "\n- If location is vague (e.g., 'metro', 'highway'), interpret as near transit hubs or major infrastructure"
            "\n- Prioritize RERA-approved properties when rera_status is specified"
            "\n- Match property_type exactly (plot, apartment, villa, commercial, etc.)"
            "\n- Consider 'near' field for proximity requirements"
            "\n\n"
            "Output format: Return a JSON object with this structure:"
            "\n{"
            "\n  'candidates': ["
            "\n    {"
            "\n      'id': 'unique_listing_id',"
            "\n      'title': 'property title',"
            "\n      'location': 'specific location/address',"
            "\n      'price_inr': numeric_price,"
            "\n      'source': 'data_source_name',"
            "\n      'rera_status': 'approved/pending/na',"
            "\n      'builder_name': 'builder or developer name'"
            "\n    }"
            "\n  ],"
            "\n  'total_found': number_of_results,"
            "\n  'search_params': original_search_criteria_used"
            "\n}"
            "\n\n"
            "Return up to 25 high-quality candidates. Prioritize listings that best match the search criteria."
            "\nReturn ONLY the JSON response, no additional text."
        )
        try:
            search_agent = Agent(
                name="Search Listings Agent",
                instructions=system_prompt,
                output_type=SearchListingsOutputSchema(),
                model="gpt-4o-mini")
            
            # Format the search payload as input
            search_input = f"Search for properties with these criteria: {json.dumps(search_payload, indent=2)}"
            
            with trace("Search Listings"):
                result = await Runner.run(search_agent, search_input)
            
            logger.info("Search Results: %s", json.dumps(result.final_output, indent=2))
            return result.final_output
            
        except Exception as e:
            print(f"Error in search_listings: {e}")
            # Return a fallback result
            return {
                "candidates": [],
                "total_found": 0,
                "search_params": search_payload,
                "error": str(e)
            }

    async def invoke(self, context: RequestContext) -> str:
        """
        Main entry point for SearchListingsAgent.
        Expects input to be search criteria payload.
        """
        try:
            user_input = context.get_user_input()
            
            # Parse user input as search payload
            # This could be JSON string or already a dict
            if isinstance(user_input, str):
                try:
                    search_payload = json.loads(user_input)
                except json.JSONDecodeError:
                    # If not JSON, treat as a general search query
                    search_payload = {"query": user_input}
            else:
                search_payload = user_input
            
            # Perform the search
            search_result = await self.search_listings(search_payload)
            
            # Return formatted response
            response = {
                "agent": "search_listings",
                "status": "success",
                "result": search_result
            }
            
            return json.dumps(response, indent=2)
            
        except Exception as e:
            logger.error(f"Error in SearchListingsAgent.invoke: {e}")
            error_response = {
                "agent": "search_listings",
                "status": "error",
                "error": str(e)
            }
            return json.dumps(error_response, indent=2)
    