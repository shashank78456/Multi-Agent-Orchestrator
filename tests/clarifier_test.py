import pytest

from agents.clarifier import Clarifier
from core.state import SystemState


class FakeLLM:
    def __init__(self, response):
        self.response = response

    async def generate_json(self, prompt):
        return self.response


@pytest.mark.asyncio
async def test_vague_query():
    state = SystemState(query="help")

    clarifier = Clarifier(
        FakeLLM(
            {
                "needs_clarification": True,
                "clarification_question": "What would you like help with?",
            }
        )
    )

    await clarifier.check(state)

    assert state.clarification_checked is True
    assert state.needs_clarification is True
    assert state.clarification_question == "What would you like help with?"


@pytest.mark.asyncio
async def test_clear_query():
    state = SystemState(query="Research operating systems")

    clarifier = Clarifier(
        FakeLLM(
            {
                "needs_clarification": False,
                "clarification_question": None,
            }
        )
    )

    await clarifier.check(state)

    assert state.clarification_checked is True
    assert state.needs_clarification is False
    assert state.clarification_question is None


def test_apply_answer():
    state = SystemState(
        query="help",
        clarification_checked=True,
        needs_clarification=True,
    )

    clarifier = Clarifier(FakeLLM({}))

    clarifier.apply_answer(state, "Research operating systems")

    assert state.needs_clarification is False
    assert (
        "Additional context: Research operating systems"
        in state.query
    )


def test_empty_answer():
    state = SystemState(
        query="help",
        clarification_checked=True,
        needs_clarification=True,
    )

    clarifier = Clarifier(FakeLLM({}))

    with pytest.raises(ValueError):
        clarifier.apply_answer(state, "   ")


@pytest.mark.asyncio
async def test_invalid_clarifier_response():
    state = SystemState(query="Research operating systems")

    clarifier = Clarifier(
        FakeLLM({"needs_clarification": "no"})
    )

    with pytest.raises(ValueError):
        await clarifier.check(state)