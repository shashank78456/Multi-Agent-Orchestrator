import pytest

import main as app

from core.dag import get_ready_nodes
from core.state import SystemState, NodeStatus
from storage import load_state


class ImmediateExecutor:

    async def execute_ready(self, state):

        for node in get_ready_nodes(state.dag):

            node.status = NodeStatus.SUCCESS
            node.output = f"Completed {node.id}"

        return state


@pytest.mark.asyncio
async def test_research_workflow(
    monkeypatch,
    tmp_path,
):

    monkeypatch.setattr(
        app,
        "Executor",
        ImmediateExecutor,
    )

    state = SystemState(
        query="Research databases"
    )

    filename = str(tmp_path / "state.json")

    completed = await app.run_workflow(
        state,
        filename,
    )

    assert all(
        node.status == NodeStatus.SUCCESS
        for node in completed.dag.values()
    )

    restored = load_state(filename)

    assert restored.phase.value == "done"


@pytest.mark.asyncio
async def test_action_workflow(
    monkeypatch,
    tmp_path,
):

    monkeypatch.setattr(
        app,
        "Executor",
        ImmediateExecutor,
    )

    answers = iter(["a"])

    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": next(answers),
    )

    state = SystemState(
        query="Send an email"
    )

    completed = await app.run_workflow(
        state,
        str(tmp_path / "state.json"),
    )

    assert completed.dag["perform_action"].approved is True

    assert (
        completed.dag["perform_action"].status
        == NodeStatus.SUCCESS
    )