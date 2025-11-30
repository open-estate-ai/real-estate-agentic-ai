from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from search_listings.agent import SearchListingsAgent
from a2a.utils import new_agent_text_message

class SearchListingsExecutor(AgentExecutor):

    def __init__(self, context=RequestContext):
        self.agent = SearchListingsAgent()
        self.context = context

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        result = await self.agent.invoke(context)
        await event_queue.enqueue_event(new_agent_text_message(result))
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("Cancellation not supported for SearchListingsAgent.")