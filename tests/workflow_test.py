import pytest

import main as app

from core.dag import get_ready_nodes
from core.state import SystemState, NodeStatus
from storage import load_state

class FakeWorkflowLLM:
    async def generate_json(self, prompt):
        if "clarification component" in prompt:
            return {
                "needs_clarification": False,
                "clarification_question": None,
            }

        if "Send an email" in prompt:
            return {
                "tasks": [
                    {
                        "id": "prepare_action",
                        "description": "Prepare the email.",
                        "tool": "prepare_action",
                        "depends_on": [],
                    },
                    {
                        "id": "perform_action",
                        "description": "Simulate sending the email.",
                        "tool": "mock_action",
                        "depends_on": ["prepare_action"],
                    },
                ]
            }

        return {
            "tasks": [
                {
                    "id": "respond",
                    "description": "Respond to the request.",
                    "tool": "echo",
                    "depends_on": [],
                }
            ]
        }

    async def generate_text(self, prompt):
        return "Fake LLM output"


class ImmediateExecutor:
    def __init__(self, llm):
        pass

    async def execute_ready(self, state):
        for node in get_ready_nodes(state.dag):
            node.status = NodeStatus.SUCCESS
            node.output = f"Completed {node.id}"

        return state


@pytest.mark.asyncio
async def test_research_workflow(monkeypatch, tmp_path):
    monkeypatch.setattr(app, "Executor", ImmediateExecutor)

    state = SystemState(query="Research databases")
    filename = str(tmp_path / "state.json")

    completed = await app.run_workflow(
        state,
        filename,
        llm=FakeWorkflowLLM(),
    )

    assert all(
        node.status == NodeStatus.SUCCESS
        for node in completed.dag.values()
    )

    restored = load_state(filename)

    assert restored.phase.value == "done"


@pytest.mark.asyncio
async def test_action_workflow(monkeypatch, tmp_path):
    monkeypatch.setattr(app, "Executor", ImmediateExecutor)

    answers = iter(["a"])

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": next(answers),
    )

    state = SystemState(query="Send an email")

    completed = await app.run_workflow(
        state,
        str(tmp_path / "state.json"),
        llm=FakeWorkflowLLM(),
    )

    assert completed.dag["perform_action"].approved is True

    assert (
        completed.dag["perform_action"].status
        == NodeStatus.SUCCESS
    )