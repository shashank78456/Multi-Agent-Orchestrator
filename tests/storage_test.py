from core.state import (
    SystemState,
    TaskNode,
    NodeStatus,
    Phase,
)

from storage import save_state, load_state


def test_save_and_load(tmp_path):

    state = SystemState(
        query="Research databases",
        phase=Phase.EXECUTE,
        clarification_checked=True,
        dag={
            "task": TaskNode(
                id="task",
                description="Test task",
                status=NodeStatus.SUCCESS,
                output="Completed",
            )
        },
    )

    filename = tmp_path / "state.json"

    save_state(state, str(filename))

    loaded = load_state(str(filename))

    assert loaded.query == state.query
    assert loaded.phase == state.phase
    assert loaded.dag["task"].status == NodeStatus.SUCCESS
    assert loaded.dag["task"].output == "Completed"


def test_running_task_recovery(tmp_path):

    state = SystemState(
        query="Test",
        clarification_checked=True,
        dag={
            "task": TaskNode(
                id="task",
                description="Test task",
                status=NodeStatus.RUNNING,
            )
        },
    )

    filename = tmp_path / "state.json"

    save_state(state, str(filename))

    loaded = load_state(str(filename))

    assert loaded.dag["task"].status == NodeStatus.PENDING
    assert loaded.dag["task"].output is None
    assert loaded.dag["task"].error is None