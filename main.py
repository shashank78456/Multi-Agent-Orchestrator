from core.orchestrator import Orchestrator
from core.state import Phase, SystemState

def main():
    query = input("Enter your query: ").strip()

    state = SystemState(query=query)
    orchestrator = Orchestrator()

    print("\nInitial state:")
    print(f"Query: {state.query}")
    print(f"Phase: {state.phase}")

    for _ in range(5):
        state = orchestrator.step(state)

        print(
            f"\nIteration {state.iteration_count}: "
            f"Phase = {state.phase.value}"
        )

        if state.phase == Phase.CLARIFY:
            print("Clarification is required.")
            break

        if state.phase == Phase.PLAN:
            print("Planning is required.")
            break

        if state.phase == Phase.EXECUTE:
            print("Ready to execute tasks.")
            break

        if state.phase == Phase.HITL_APPROVAL:
            print("Human approval is required.")
            break

        if state.phase == Phase.DONE:
            print("Task completed.")
            break

        if state.phase == Phase.FAILED:
            print(f"Execution failed: {state.error}")
            break


if __name__ == "__main__":
    main()