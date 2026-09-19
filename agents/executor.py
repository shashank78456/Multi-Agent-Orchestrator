import asyncio
from typing import Awaitable, Callable, Dict, Optional

from core.dag import get_ready_nodes, has_failed_nodes, validate_dag
from core.state import NodeStatus, SystemState, TaskNode

ToolFunction = Callable[[TaskNode, SystemState], Awaitable[str]]

async def mock_search(task: TaskNode, state: SystemState) -> str:
    """A deliberately mocked search tool; it does not access the internet."""
    await asyncio.sleep(0.1)
    return (
        f"[MOCK SEARCH] Information related to '{state.query}' "
        f"for task '{task.id}'."
    )

async def summarize(task: TaskNode, state: SystemState) -> str:
    raise RuntimeError("The summarize tool requires an LLM client.")


async def prepare_action(task: TaskNode, state: SystemState) -> str:
    raise RuntimeError("The prepare_action tool requires an LLM client.")


async def mock_action(task: TaskNode, state: SystemState) -> str:
    """A deliberately mocked action tool; it performs no external action."""
    await asyncio.sleep(0.1)
    return "[MOCK] Action simulated successfully. No external action was performed."


async def echo(task: TaskNode, state: SystemState) -> str:
    raise RuntimeError("The echo tool requires an LLM client.")


DEFAULT_TOOLS: Dict[str, ToolFunction] = {
    "mock_search": mock_search,
    "summarize": summarize,
    "prepare_action": prepare_action,
    "mock_action": mock_action,
    "echo": echo,
}

class Executor:
    def __init__(
        self,
        llm=None,
        tools: Optional[Dict[str, ToolFunction]] = None,
    ):
        if llm is None and tools is None:
            raise ValueError(
                "An LLM client is required when using the default tools."
            )

        self.llm = llm
        self.tools = DEFAULT_TOOLS.copy() if tools is None else tools.copy()

        if llm is not None:
            self.tools.update(
                {
                    "summarize": self._summarize,
                    "prepare_action": self._prepare_action,
                    "echo": self._echo,
                }
            )

    async def _summarize(self, task: TaskNode, state: SystemState) -> str:
        dependency_outputs = []

        for dependency_id in task.depends_on:
            dependency = state.dag[dependency_id]

            if dependency.output:
                dependency_outputs.append(
                    f"Task {dependency_id}:\n{dependency.output}"
                )

        if not dependency_outputs:
            raise ValueError(
                "Summarize task has no dependency outputs to summarize."
            )

        prompt = f"""Summarize the information below in a clear, concise response.
Do not invent facts that are not present in the supplied information.

User request: {state.query}
Task description: {task.description}

Information:
{chr(10).join(dependency_outputs)}
"""

        return await self.llm.generate_text(prompt)

    async def _prepare_action(self, task: TaskNode, state: SystemState) -> str:
        prompt = f"""Prepare a concise draft or proposal for the requested action.
Do not perform the action, claim that it has been performed, or contact any external service.

User request: {state.query}
Task description: {task.description}
"""

        return await self.llm.generate_text(prompt)

    async def _echo(self, task: TaskNode, state: SystemState) -> str:
        prompt = f"""Respond helpfully and directly to the user's request.
Do not claim to have used tools or performed external actions.

User request: {state.query}
Task description: {task.description}
"""

        return await self.llm.generate_text(prompt)

    async def _execute_node(self, node: TaskNode, state: SystemState) -> None:
        """Execute one task and update its status."""

        try:
            if not node.tool:
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
        """Execute one batch of currently ready tasks concurrently."""

        validate_dag(state.dag)

        if state.error or has_failed_nodes(state.dag):
            return state

        ready_nodes = get_ready_nodes(state.dag)

        if not ready_nodes:
            return state

        for node in ready_nodes:
            node.status = NodeStatus.RUNNING

        await asyncio.gather(*(self._execute_node(node, state) for node in ready_nodes))

        return state