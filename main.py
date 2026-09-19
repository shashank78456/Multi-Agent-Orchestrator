import asyncio
from pathlib import Path

from agents.clarifier import Clarifier
from agents.executor import Executor
from agents.planner import Planner
from core.approval import ApprovalManager
from core.llm_client import LLMClient
from core.orchestrator import Orchestrator
from core.state import Phase, SystemState
from storage import load_state, save_state

STATE_FILE = "state.json"

def save_checkpoint(state: SystemState, filename: str) -> None:
    """Save the current workflow state."""

    try:
        save_state(state, filename)
    except (OSError, ValueError) as exc:
        print(f"Warning: Could not save workflow state: {exc}")


async def run_workflow(
    state: SystemState,
    state_file: str = STATE_FILE,
    llm=None,
) -> SystemState:

    llm = llm or LLMClient()

    clarifier = Clarifier(llm)
    planner = Planner(llm)
    executor = Executor(llm)
    approval_manager = ApprovalManager()
    orchestrator = Orchestrator()

    print("\nStarting workflow...")

    while True:
        state = orchestrator.step(state)

        print(
            f"\nIteration {state.iteration_count}: "
            f"Phase = {state.phase.value}"
        )

        if state.phase == Phase.CLARIFY:
            if not state.clarification_checked:
                try:
                    await clarifier.check(state)
                except Exception as exc:
                    state.error = f"Clarification failed: {exc}"
                    save_checkpoint(state, state_file)
                    continue

                save_checkpoint(state, state_file)

            if state.needs_clarification:
                print(
                    state.clarification_question
                    or "Please provide more details about your request."
                )

                while True:
                    answer = input("Your answer: ").strip()

                    try:
                        clarifier.apply_answer(state, answer)
                        break
                    except ValueError as exc:
                        print(exc)

                save_checkpoint(state, state_file)

            continue

        if state.phase == Phase.PLAN:
            try:
                await planner.create_plan(state)
            except Exception as exc:
                state.error = f"Planning failed: {exc}"

            save_checkpoint(state, state_file)
            continue

        if state.phase == Phase.EXECUTE:
            save_checkpoint(state, state_file)
            await executor.execute_ready(state)
            save_checkpoint(state, state_file)
            continue

        if state.phase == Phase.HITL_APPROVAL:
            pending_nodes = approval_manager.get_pending_approvals(state)

            for node in pending_nodes:
                print(f"\nApproval required for task: {node.id}")
                print(f"Description: {node.description}")

                while True:
                    decision = input(
                        "Approve or reject? [a/r]: "
                    ).strip().lower()

                    if decision in {"a", "approve", "y", "yes"}:
                        approval_manager.approve_task(state, node.id)
                        print(f"Task '{node.id}' approved.")
                        save_checkpoint(state, state_file)
                        break

                    if decision in {"r", "reject", "n", "no"}:
                        approval_manager.reject_task(state, node.id)
                        print(f"Task '{node.id}' rejected.")
                        save_checkpoint(state, state_file)
                        break

                    print("Please enter 'a' to approve or 'r' to reject.")

                if state.error:
                    break
            continue

        if state.phase == Phase.DONE:
            print("\nWorkflow completed successfully.")
            print("\nTask outputs:")

            for node in state.dag.values():
                print(f"\n{node.id}:")
                print(node.output or "(No output)")

            save_checkpoint(state, state_file)
            return state

        if state.phase == Phase.FAILED:
            print(f"\nWorkflow failed: {state.error}")

            for node in state.dag.values():
                if node.error:
                    print(f"{node.id}: {node.error}")

            save_checkpoint(state, state_file)
            return state

def main() -> None:
    print("1. Start a new workflow")
    print("2. Resume a previous workflow")
    choice = input("\nChoose an option [1/2]: ").strip()

    if(choice == "1"):
        query = input("\nEnter your query: ").strip()
        state = SystemState(query=query)

    elif(choice == "2"):
        if not Path(STATE_FILE).exists():
            print(f"\nNo saved workflow found at '{STATE_FILE}'.")
            return

        try:
            state = load_state(STATE_FILE)
        except (OSError, ValueError) as exc:
            print(f"\nCould not load saved workflow: {exc}")
            return

        print(f"\nResuming workflow for: {state.query}")

    else:
        print("\nInvalid Input")
        return

    try:
        asyncio.run(run_workflow(state))
    except (ValueError, RuntimeError) as exc:
        print(f"\nCould not start workflow: {exc}")


if __name__ == "__main__":
    main()