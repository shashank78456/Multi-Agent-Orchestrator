from core.dag import validate_dag
from core.state import SystemState, TaskNode
from agents.executor import DEFAULT_TOOLS

class Planner:
    def __init__(self, llm):
        self.llm = llm

    async def create_plan(self, state: SystemState) -> SystemState:
        """Generate a task DAG from the user's query using the LLM."""

        if not state.clarification_checked:
            raise ValueError("Clarification has not been completed.")

        if state.needs_clarification:
            raise ValueError("The query still needs clarification.")

        if state.dag:
            raise ValueError("A plan already exists for this query.")

        available_tools = ", ".join(sorted(DEFAULT_TOOLS))

        prompt = f"""You are the planning component of a task orchestrator.

Create a small directed acyclic graph (DAG) of tasks that can fulfill the user's request.
Use only these tool names: {available_tools}.

Available tool meanings:
- mock_search: produce mocked search information; it does not access the internet.
- summarize: summarize outputs from dependency tasks.
- prepare_action: prepare or draft an action; it does not perform it.
- mock_action: simulate an external action; it never performs a real external action.
- echo: generate a direct response to the user.

Planning rules:
1. Create only the tasks needed for this request. Use concise, unique task IDs.
2. Each task must have an id, description, tool, and depends_on list.
3. Dependencies must refer to other task IDs in this same response.
4. The graph must be acyclic.
5. For a request involving an external side effect (for example sending, publishing,
   deleting, purchasing, or submitting), create a prepare_action task followed by a
   mock_action task that depends on it.
6. Never use mock_action for an ordinary informational response.
7. Do not claim that mock_search accesses the internet or that mock_action performs a
   real external action.

User request:
{state.query}

Return only a JSON object in this format:
{{
  "tasks": [
    {{
      "id": "task_id",
      "description": "What this task does",
      "tool": "one of the allowed tool names",
      "depends_on": [],
      "requires_approval": false
    }}
  ]
}}

Set requires_approval to true for mock_action tasks. The application will enforce this
requirement independently as well.
"""

        result = await self.llm.generate_json(prompt)
        tasks = result.get("tasks")

        if not isinstance(tasks, list) or not tasks:
            raise ValueError(
                "Planner response must contain a non-empty 'tasks' list."
            )

        dag = {}

        for task_data in tasks:
            if not isinstance(task_data, dict):
                raise ValueError("Every planner task must be a JSON object.")

            task_id = task_data.get("id")
            description = task_data.get("description")
            tool = task_data.get("tool")
            dependencies = task_data.get("depends_on", [])
            requires_approval = task_data.get("requires_approval", False)

            if not isinstance(task_id, str) or not task_id.strip():
                raise ValueError(
                    "Every planner task must have a non-empty string ID."
                )

            if not isinstance(description, str) or not description.strip():
                raise ValueError(
                    f"Task '{task_id}' must have a non-empty description."
                )

            if not isinstance(tool, str) or tool not in DEFAULT_TOOLS:
                raise ValueError(
                    f"Task '{task_id}' uses an unknown tool: {tool}."
                )

            if not isinstance(dependencies, list) or not all(
                isinstance(dependency, str) and dependency
                for dependency in dependencies
            ):
                raise ValueError(
                    f"Task '{task_id}' has an invalid depends_on list."
                )

            if not isinstance(requires_approval, bool):
                raise ValueError(
                    f"Task '{task_id}' must have a boolean requires_approval value."
                )

            if task_id in dag:
                raise ValueError(
                    f"Planner returned duplicate task ID '{task_id}'."
                )

            if tool == "mock_action":
                requires_approval = True

            dag[task_id] = TaskNode(
                id=task_id,
                description=description.strip(),
                tool=tool,
                depends_on=dependencies,
                requires_approval=requires_approval,
                approved=False,
            )

        validate_dag(dag)
        state.dag = dag

        return state