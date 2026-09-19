import asyncio
from typing import Awaitable, Callable, Dict, Optional

from core.dag import get_ready_nodes, has_failed_nodes, validate_dag
from core.state import NodeStatus, SystemState, TaskNode

ToolFunction = Callable[[TaskNode, SystemState], Awaitable[str]]

async def mock_search(task: TaskNode, state: SystemState) -> str:
    await asyncio.sleep(1)
    
    return (f"Search result for task '{task.id}': Information about {state.query}")

async def summarize(task: TaskNode, state: SystemState) -> str:
    await asyncio.sleep(0.5)
    
    results = []
    for dependency_id in task.depends_on:
        dependency = state.dag[dependency_id]
        if dependency.output:
            results.append(dependency.output)

    return ("Summary based on the gathered information:\n" + "\n".join(results))

async def prepare_action(task: TaskNode, state: SystemState) -> str:
    await asyncio.sleep(0.5)

    return f"Prepared action for: {state.query}"


async def mock_action(task: TaskNode, state: SystemState,) -> str:

    await asyncio.sleep(1)

    return ("[MOCK] Action simulated successfully. No external action was actually performed.")


async def echo(task: TaskNode, state: SystemState) -> str:
    await asyncio.sleep(0.2)

    return f"Received request: {state.query}"

DEFAULT_TOOLS: Dict[str, ToolFunction] = {
    "mock_search": mock_search,
    "summarize": summarize,
    "prepare_action": prepare_action,
    "mock_action": mock_action,
    "echo": echo,
}

class Executor:
    
    def __init__(self, llm):
        self.llm = llm
    
    def __init__(self, tools: Optional[Dict[str, ToolFunction]]=None):
        self.tools = DEFAULT_TOOLS.copy() if tools is None else tools
    
    async def _execute_node(self, node: TaskNode, state: SystemState) -> None:
        """
        Execute one task and update its status.
        """
        
        try:
            if(not node.tool):
                raise ValueError(f"Task '{node.id}' has no tool assigned.")

            tool = self.tools.get(node.tool)
            if tool is None:
                raise ValueError(f"Unknown tool: {node.tool}")

            output = await tool(node, state)

            node.output = output
            node.status = NodeStatus.SUCCESS
            node.error = None

        except Exception as exc:
            node.status = NodeStatus.FAILED
            node.error = str(exc)

    
    async def execute_ready(self, state: SystemState) -> SystemState:
        """
        Execute all currently ready tasks concurrently.

        This executes one batch. The Orchestrator can be called
        again to identify and execute the next batch.
        """

        validate_dag(state.dag)
        
        if(state.error or has_failed_nodes(state.dag)):
            return state
        
        ready_nodes = get_ready_nodes(state.dag)
        if(not ready_nodes):
            return state

        for node in ready_nodes:
            node.status = NodeStatus.RUNNING

        await asyncio.gather(*[self._execute_node(node, state) for node in ready_nodes])

        return state
    