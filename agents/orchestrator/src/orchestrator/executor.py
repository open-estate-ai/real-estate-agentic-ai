from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from orchestrator.agent import OrchestratorAgent
from a2a.utils import new_agent_text_message

class OrchestratorExecutor(AgentExecutor):

    def __init__(self, context=RequestContext):
        self.agent = OrchestratorAgent()
        self.context = context

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        result = await self.agent.invoke(context)
        await event_queue.enqueue_event(new_agent_text_message(result))
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("Cancellation not supported for OrchestratorAgent")