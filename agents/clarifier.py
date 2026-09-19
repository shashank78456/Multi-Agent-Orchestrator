from core.state import SystemState

class Clarifier:
    def __init__(self, llm):
        self.llm = llm

    async def check(self, state: SystemState) -> SystemState:
        """Check with the LLM whether the user's query needs clarification."""

        if state.clarification_checked:
            return state

        prompt = f"""You are the clarification component of a task orchestrator.

Decide whether the user's request contains enough information to create a useful task plan.
Ask for clarification only when important information is missing. Do not ask unnecessary
questions for requests that are already actionable.

User request:
{state.query}

Return only a JSON object with this exact structure:
{{
  "needs_clarification": true,
  "clarification_question": "A single concise question"
}}

When clarification is not needed, return needs_clarification as false and
clarification_question as null.
"""

        result = await self.llm.generate_json(prompt)

        needs_clarification = result.get("needs_clarification")
        question = result.get("clarification_question")

        if not isinstance(needs_clarification, bool):
            raise ValueError(
                "Clarifier response must contain a boolean 'needs_clarification'."
            )

        if needs_clarification:
            if not isinstance(question, str) or not question.strip():
                raise ValueError(
                    "Clarifier must provide a question when clarification is needed."
                )
            state.clarification_question = question.strip()
        else:
            state.clarification_question = None

        state.needs_clarification = needs_clarification
        state.clarification_checked = True
        return state

    def apply_answer(self, state: SystemState, answer: str) -> SystemState:
        """Incorporate the user's clarification into the original query."""

        answer = answer.strip()

        if not state.needs_clarification:
            raise ValueError("The query needs no clarification")

        if not answer:
            raise ValueError("Clarification answer cannot be empty")

        state.clarification_answer = answer
        state.query = f"{state.query}\nAdditional context: {answer}".strip()
        state.needs_clarification = False
        state.clarification_question = None

        return state
