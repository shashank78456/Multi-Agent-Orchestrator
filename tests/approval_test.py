import pytest

from core.approval import ApprovalManager
from core.state import SystemState, TaskNode, NodeStatus


def create_state():

    return SystemState(
        query="Send email",
        clarification_checked=True,
        dag={
            "prepare": TaskNode(
                id="prepare",
                description="Prepare email",
            ),

            "perform": TaskNode(
                id="perform",
                description="Send email",
                depends_on=["prepare"],
                requires_approval=True,
            ),
        },
    )


def test_approve_task():

    state = create_state()

    state.dag["prepare"].status = NodeStatus.SUCCESS

    manager = ApprovalManager()

    node = manager.approve_task(state, "perform")

    assert node.approved is True
    assert manager.get_pending_approvals(state) == []


def test_reject_task():

    state = create_state()

    state.dag["prepare"].status = NodeStatus.SUCCESS

    manager = ApprovalManager()

    node = manager.reject_task(state, "perform")

    assert node.status == NodeStatus.FAILED
    assert state.error is not None


def test_invalid_approval():

    state = create_state()

    manager = ApprovalManager()

    with pytest.raises(ValueError):

        manager.approve_task(state, "perform")