from core.state import Phase, SystemState, TaskNode, NodeStatus


def test_state_defaults():

    state = SystemState(query="Hello")

    assert state.phase == Phase.CLARIFY
    assert state.clarification_checked is False
    assert state.needs_clarification is False
    assert state.dag == {}
    assert state.iteration_count == 0


def test_state_serialization():

    state = SystemState(query="Research databases")

    data = state.model_dump(mode="json")

    restored = SystemState.model_validate(data)

    assert restored.query == state.query
    assert restored.phase == state.phase


def test_task_node_defaults():

    node = TaskNode(
        id="task1",
        description="Test task",
    )

    assert node.status == NodeStatus.PENDING
    assert node.approved is False
    assert node.depends_on == []
    assert node.output is None