import asyncio

from agents.clarifier import Clarifier
from agents.executor import Executor
from agents.planner import Planner
from core.approval import ApprovalManager
from core.orchestrator import Orchestrator
from core.state import Phase, SystemState

async def run_workflow(query: str) -> None:
    state = SystemState(query=query)

    clarifier = Clarifier()
    planner = Planner()
    executor = Executor()
    approval_manager = ApprovalManager()
    orchestrator = Orchestrator()

    print("\nStarting workflow...")

    while True:
        state = orchestrator.step(state)

        print(f"\nIteration {state.iteration_count}: Phase = {state.phase.value}")

        if state.phase == Phase.CLARIFY:
            if not state.clarification_checked:
                clarifier.check(state)

            if state.needs_clarification:
                print(state.clarification_question)
                
                while True:
                    answer = input("Your answer: ").strip()
                    try:
                        clarifier.apply_answer(state, answer)
                        break

                    except ValueError as exc:
                        print(exc)
            continue

        if state.phase == Phase.PLAN:
            try:
                planner.create_plan(state)

            except ValueError as exc:
                state.error = f"Planning failed: {exc}"

            continue

        if state.phase == Phase.EXECUTE:
            await executor.execute_ready(state)
            continue

        if state.phase == Phase.HITL_APPROVAL:
            pending_nodes = (approval_manager.get_pending_approvals(state))

            for node in pending_nodes:
                print(f"\nApproval required for task: {node.id}")
                print(f"Description: {node.description}")

                while True:
                    decision = input("Approve or reject? [a/r]: ").strip().lower()

                    if decision in {"a", "approve", "y", "yes"}:
                        approval_manager.approve_task(state, node.id)
                        print(f"Task '{node.id}' approved.")
                        break

                    elif decision in {"r", "reject", "n", "no"}:
                        approval_manager.reject_task(state, node.id)
                        print(f"Task '{node.id}' rejected.")
                        break

                    else:
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

            return

        if state.phase == Phase.FAILED:
            print(f"\nWorkflow failed: {state.error}")

            for node in state.dag.values():
                if node.error:
                    print(f"{node.id}: {node.error}")
            return

def main() -> None:
    query = input("Enter your query: ").strip()
    asyncio.run(run_workflow(query))

if __name__ == "__main__":
    main()