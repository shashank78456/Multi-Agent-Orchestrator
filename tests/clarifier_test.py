import pytest

from agents.clarifier import Clarifier
from core.state import SystemState


def test_vague_query():

    state = SystemState(query="help")

    clarifier = Clarifier()
    clarifier.check(state)

    assert state.clarification_checked is True
    assert state.needs_clarification is True
    assert state.clarification_question is not None


def test_clear_query():

    state = SystemState(
        query="Research operating systems"
    )

    clarifier = Clarifier()
    clarifier.check(state)

    assert state.clarification_checked is True
    assert state.needs_clarification is False
    assert state.clarification_question is None


def test_apply_answer():

    state = SystemState(query="help")

    clarifier = Clarifier()

    clarifier.check(state)

    clarifier.apply_answer(
        state,
        "Research operating systems",
    )

    assert state.needs_clarification is False
    assert "Additional context: Research operating systems" in state.query


def test_empty_answer():

    state = SystemState(query="help")

    clarifier = Clarifier()
    clarifier.check(state)

    with pytest.raises(ValueError):

        clarifier.apply_answer(state, "   ")