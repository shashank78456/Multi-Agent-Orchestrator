import pytest
from agents.planner import Planner
from core.state import SystemState

class FakeLLM:
    def __init__(self, response):
        self.response = response

    async def generate_json(self, prompt):
        return self.response


def create_state(query):
    return SystemState(
        query=query,
        clarification_checked=True,
    )


@pytest.mark.asyncio
async def test_research_plan():
    state = create_state("Research databases")

    llm = FakeLLM(
        {
            "tasks": [
                {
                    "id": "search_primary",
                    "description": "Find primary information about databases.",
                    "tool": "mock_search",
                    "depends_on": [],
                },
                {
                    "id": "search_secondary",
                    "description": "Find additional information about databases.",
                    "tool": "mock_search",
                    "depends_on": [],
                },
                {
                    "id": "summarize",
                    "description": "Summarize the gathered information.",
                    "tool": "summarize",
                    "depends_on": [
                        "search_primary",
                        "search_secondary",
                    ],
                },
            ]
        }
    )

    await Planner(llm).create_plan(state)

    assert set(state.dag) == {
        "search_primary",
        "search_secondary",
        "summarize",
    }

    assert state.dag["summarize"].depends_on == [
        "search_primary",
        "search_secondary",
    ]


@pytest.mark.asyncio
async def test_action_plan_always_requires_approval():
    state = create_state("Send an email")

    llm = FakeLLM(
        {
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
                    "requires_approval": False,
                },
            ]
        }
    )

    await Planner(llm).create_plan(state)

    assert state.dag["perform_action"].requires_approval is True
    assert state.dag["perform_action"].depends_on == [
        "prepare_action"
    ]
    assert state.dag["perform_action"].approved is False


@pytest.mark.asyncio
async def test_unknown_tool_is_rejected():
    state = create_state("Do something")

    llm = FakeLLM(
        {
            "tasks": [
                {
                    "id": "task",
                    "description": "Run an unregistered tool.",
                    "tool": "shell",
                    "depends_on": [],
                }
            ]
        }
    )

    with pytest.raises(ValueError, match="unknown tool"):
        await Planner(llm).create_plan(state)


@pytest.mark.asyncio
async def test_cyclic_dag_is_rejected():
    state = create_state("Do two dependent tasks")

    llm = FakeLLM(
        {
            "tasks": [
                {
                    "id": "a",
                    "description": "Task A",
                    "tool": "echo",
                    "depends_on": ["b"],
                },
                {
                    "id": "b",
                    "description": "Task B",
                    "tool": "echo",
                    "depends_on": ["a"],
                },
            ]
        }
    )

    with pytest.raises(ValueError, match="cycle"):
        await Planner(llm).create_plan(state)


@pytest.mark.asyncio
async def test_malformed_task_list_is_rejected():
    state = create_state("Do something")

    with pytest.raises(ValueError, match="tasks"):
        await Planner(
            FakeLLM({"tasks": "not a list"})
        ).create_plan(state)


@pytest.mark.asyncio
async def test_fallback_plan_is_generated_by_llm():
    state = create_state("Hello there")

    llm = FakeLLM(
        {
            "tasks": [
                {
                    "id": "respond",
                    "description": "Respond to the greeting.",
                    "tool": "echo",
                    "depends_on": [],
                }
            ]
        }
    )

    await Planner(llm).create_plan(state)

    assert set(state.dag) == {"respond"}
    assert state.dag["respond"].tool == "echo"