from a2a.types import (AgentCapabilities, AgentSkill, AgentCard)
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
import uvicorn
from search_listings.executor import SearchListingsExecutor
from a2a.server.tasks import InMemoryTaskStore
from search_listings.config import validate_config



def main():
    if not validate_config():
        print("Missing required configuration. Exiting.")
        exit(1)

    skill = AgentSkill(
        id="search_listings",
        name="Search Listings",
        description="Search for real estate listings based on user criteria.",
        tags=["search", "real estate"],
        examples=["Find plots under ₹80 lakh near metro stations."]
    )
    
    public_agent_card = AgentCard(
        name = "Search Listings Agent",
        description = "An agent that specializes in searching for real estate listings.",
        url = "http://localhost:9001/",
        version = "1.0.0",
        default_input_modes = ["text"],
        default_output_modes = ["text"],
        capabilities = AgentCapabilities(streaming=True),
        skills = [skill],
        supports_authenticated_extended_card=True,
    )
    request_handler = DefaultRequestHandler(agent_executor=SearchListingsExecutor(), task_store=InMemoryTaskStore())
    server = A2AStarletteApplication(agent_card=public_agent_card, http_handler=request_handler)
    uvicorn.run(server.build(), host='0.0.0.0', port=9001)

if __name__ == "__main__":
    main()
