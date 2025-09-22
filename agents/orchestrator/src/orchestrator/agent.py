from a2a.server.agent_execution import RequestContext
class OrchestratorAgent:
    async def invoke(self, context: RequestContext) -> str:
        print(context.get_user_input())
        return "Orchestrator agent invoked!"