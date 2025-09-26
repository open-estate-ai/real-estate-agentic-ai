"""DAG Executor for Orchestrator Agent.

This module handles the execution of planned DAG tasks by calling appropriate
downstream agents. It processes the planner output and executes tasks in
dependency order.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import AgentCard, MessageSendParams, SendMessageRequest

from orchestrator.planner import DAGTask, PlannerOutput

logger = logging.getLogger(__name__)


class DAGExecutor:
    """Executes DAG tasks by calling appropriate downstream agents."""
    
    def __init__(self):
        self.agent_endpoints = {
            "search_listings": "http://localhost:9001",
            # "legal_check": "http://localhost:9002", 
            # "valuation_analysis": "http://localhost:9003",
            # "verification_scan": "http://localhost:9004",
            # "summarization": "http://localhost:9005",
        }
        self.task_results: Dict[str, Any] = {}
        
    async def execute_dag(self, planner_output: PlannerOutput) -> Dict[str, Any]:
        """Execute all tasks in the DAG according to dependencies."""
        logger.info(f"Starting DAG execution with {len(planner_output.dag)} tasks")
        
        # Build dependency graph
        tasks_by_id = {task.task_id: task for task in planner_output.dag}
        
        # Execute tasks in dependency order
        executed_tasks = set()
        
        while len(executed_tasks) < len(planner_output.dag):
            # Find tasks that can be executed (all dependencies met)
            ready_tasks = [
                task for task in planner_output.dag
                if task.task_id not in executed_tasks and
                all(dep_id in executed_tasks for dep_id in task.depends_on)
            ]
            
            if not ready_tasks:
                raise RuntimeError("Circular dependency or unresolvable dependencies in DAG")
            
            # Execute ready tasks (could be parallel, but keeping sequential for now)
            for task in ready_tasks:
                try:
                    logger.info(f"Executing task: {task.task_id} ({task.task_type})")
                    result = await self._execute_task(task)
                    self.task_results[task.task_id] = result
                    executed_tasks.add(task.task_id)
                    logger.info(f"Task {task.task_id} completed successfully")
                except Exception as e:
                    logger.error(f"Task {task.task_id} failed: {e}")
                    # Store error result
                    self.task_results[task.task_id] = {
                        "error": str(e),
                        "status": "failed"
                    }
                    executed_tasks.add(task.task_id)
        
        return {
            "status": "completed",
            "task_results": self.task_results,
            "execution_summary": {
                "total_tasks": len(planner_output.dag),
                "successful_tasks": len([r for r in self.task_results.values() if "error" not in r]),
                "failed_tasks": len([r for r in self.task_results.values() if "error" in r])
            }
        }
    
    async def _execute_task(self, task: DAGTask) -> Dict[str, Any]:
        """Execute a single task by calling the appropriate agent."""
        
        # Check if agent endpoint exists
        if task.task_type not in self.agent_endpoints:
            raise ValueError(f"No endpoint configured for task type: {task.task_type}")
        
        endpoint = self.agent_endpoints[task.task_type]
        
        # Resolve payload template with previous task results
        resolved_payload = self._resolve_payload_template(task.payload_template)
        
        # Call the agent
        agent_response = await self._call_agent(
            endpoint=endpoint,
            task_type=task.task_type,
            payload=resolved_payload,
            agent_prompt=task.agent_prompt,
            timeout_ms=task.timeout_ms
        )
        
        return agent_response
    
    def _resolve_payload_template(self, payload_template: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve template placeholders with actual values from previous tasks."""
        resolved = {}
        
        for key, value in payload_template.items():
            if isinstance(value, str) and "{{" in value and "}}" in value:
                # Extract placeholder like {{t1_search.candidates.ids}}
                resolved[key] = self._resolve_placeholder(value)
            else:
                resolved[key] = value
        
        return resolved
    
    def _resolve_placeholder(self, placeholder: str) -> Any:
        """Resolve a single placeholder like {{t1_search.candidates.ids}}."""
        # Remove {{ and }}
        path = placeholder.strip("{}").strip()
        
        # Split into parts: t1_search.candidates.ids -> [t1_search, candidates, ids]
        parts = path.split(".")
        task_id = parts[0]
        
        if task_id not in self.task_results:
            logger.warning(f"Task result not found for {task_id}, returning placeholder as-is")
            return placeholder
        
        # Navigate through the result object
        result = self.task_results[task_id]
        try:
            for part in parts[1:]:
                if isinstance(result, dict):
                    result = result[part]
                else:
                    # If we need to access an array or other structure
                    result = getattr(result, part, None)
            return result
        except (KeyError, AttributeError, TypeError):
            logger.warning(f"Could not resolve placeholder {placeholder}, returning as-is")
            return placeholder
    
    async def _call_agent(self, endpoint: str, task_type: str, payload: Dict[str, Any], 
                         agent_prompt: Optional[str], timeout_ms: int) -> Dict[str, Any]:
        """Call a downstream agent via A2A protocol."""
        
        timeout_config = httpx.Timeout(timeout_ms / 1000.0)  # Convert ms to seconds
        
        async with httpx.AsyncClient(timeout=timeout_config) as httpx_client:
            try:
                # Get agent card
                resolver = A2ACardResolver(
                    httpx_client=httpx_client,
                    base_url=endpoint,
                )
                
                agent_card = await resolver.get_agent_card()
                
                # Create client
                client = A2AClient(
                    httpx_client=httpx_client, 
                    agent_card=agent_card
                )
                
                # Prepare message - combine agent_prompt with payload
                if agent_prompt:
                    message_text = f"{agent_prompt}\n\nPayload: {json.dumps(payload, indent=2)}"
                else:
                    message_text = json.dumps(payload, indent=2)
                
                # Send message
                send_payload = {
                    'message': {
                        'role': 'user',
                        'parts': [
                            {'kind': 'text', 'text': message_text}
                        ],
                        'messageId': uuid4().hex,
                    },
                }
                
                request = SendMessageRequest(
                    id=str(uuid4()), 
                    params=MessageSendParams(**send_payload)
                )
                
                response = await client.send_message(request)
                
                # Extract the actual response content
                response_data = response.model_dump(mode='json', exclude_none=True)
                
                # Try to parse JSON from the response if it's a string
                if isinstance(response_data.get('content'), str):
                    try:
                        parsed_content = json.loads(response_data['content'])
                        response_data['content'] = parsed_content
                    except json.JSONDecodeError:
                        # Keep as string if not valid JSON
                        pass
                
                return {
                    "status": "success",
                    "agent": task_type,
                    "endpoint": endpoint,
                    "response": response_data
                }
                
            except Exception as e:
                logger.error(f"Failed to call agent {task_type} at {endpoint}: {e}")
                return {
                    "status": "error",
                    "agent": task_type,
                    "endpoint": endpoint,
                    "error": str(e)
                }


# Convenience function for easy usage
async def execute_dag(planner_output: PlannerOutput) -> Dict[str, Any]:
    """Execute a DAG plan by calling appropriate agents."""
    executor = DAGExecutor()
    return await executor.execute_dag(planner_output)