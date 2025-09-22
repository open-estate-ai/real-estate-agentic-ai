from a2a.types import (AgentCapabilities, AgentSkill, AgentCard)
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
import uvicorn
from orchestrator.executor import OrchestratorExecutor
from a2a.server.tasks import InMemoryTaskStore

def main():
    skill = AgentSkill(
        id="orchestrator",
        name="Orchestrator",
        description="Orchestrates multiple agents to achieve complex tasks.",
        tags=["orchestration", "coordination"],
        examples=["Find RERA-approved plots under ₹80 lakh near metro, good for investment."]
    )
    
    public_agent_card = AgentCard(
        name = "Orchestrator Agent",
        description = "An agent that orchestrates multiple specialized agents to achieve complex tasks.",
        url = "http://localhost:9999/",
        version = "1.0.0",
        default_input_modes = ["text"],
        default_output_modes = ["text"],
        capabilities = AgentCapabilities(streaming=True),
        skills = [skill],
        supports_authenticated_extended_card=True,
    )
    request_handler = DefaultRequestHandler(agent_executor=OrchestratorExecutor(), task_store=InMemoryTaskStore())
    server = A2AStarletteApplication(agent_card=public_agent_card, http_handler=request_handler)
    uvicorn.run(server.build(), host='0.0.0.0', port=9999)
    
if __name__ == "__main__":
    main()
