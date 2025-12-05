from agents.planner import Planner
from core.state import SystemState


def create_state(query):

    return SystemState(
        query=query,
        clarification_checked=True,
    )


def test_research_plan():

    state = create_state("Research databases")

    Planner().create_plan(state)

    assert set(state.dag.keys()) == {
        "search_primary",
        "search_secondary",
        "summarize",
    }

    assert state.dag["summarize"].depends_on == [
        "search_primary",
        "search_secondary",
    ]


def test_action_plan():

    state = create_state("Send an email")

    Planner().create_plan(state)

    assert state.dag["perform_action"].requires_approval is True

    assert state.dag["perform_action"].depends_on == [
        "prepare_action",
    ]


def test_fallback_plan():

    state = create_state("Hello there")

    Planner().create_plan(state)

    assert set(state.dag.keys()) == {"respond"}

    assert state.dag["respond"].tool == "echo"