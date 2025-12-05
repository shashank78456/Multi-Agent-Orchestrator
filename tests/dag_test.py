import pytest

from core.dag import (
    validate_dag,
    get_ready_nodes,
    get_approval_nodes,
)

from core.state import TaskNode, NodeStatus


def create_node(node_id, dependencies=None, **kwargs):

    return TaskNode(
        id=node_id,
        description=node_id,
        depends_on=dependencies or [],
        **kwargs,
    )


def test_valid_dag():

    dag = {
        "first": create_node("first"),
        "second": create_node("second", ["first"]),
    }

    validate_dag(dag)


@pytest.mark.parametrize("dag", [

    {
        "a": create_node("a", ["missing"])
    },

    {
        "a": create_node("a", ["a"])
    },

    {
        "a": create_node("a", ["b"]),
        "b": create_node("b", ["a"]),
    },

    {
        "a": create_node("different")
    },

    {
        "a": create_node("a", ["b", "b"]),
        "b": create_node("b"),
    },

])
def test_invalid_dag(dag):

    with pytest.raises(ValueError):
        validate_dag(dag)


def test_ready_nodes():

    dag = {
        "first": create_node("first"),
        "second": create_node("second", ["first"]),
    }

    ready = get_ready_nodes(dag)

    assert [node.id for node in ready] == ["first"]

    dag["first"].status = NodeStatus.SUCCESS

    ready = get_ready_nodes(dag)

    assert [node.id for node in ready] == ["second"]


def test_approval_nodes():

    dag = {
        "prepare": create_node("prepare"),

        "perform": create_node(
            "perform",
            ["prepare"],
            requires_approval=True,
        ),
    }

    assert get_approval_nodes(dag) == []

    dag["prepare"].status = NodeStatus.SUCCESS

    approvals = get_approval_nodes(dag)

    assert len(approvals) == 1
    assert approvals[0].id == "perform"