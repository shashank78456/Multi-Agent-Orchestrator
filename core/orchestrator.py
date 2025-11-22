from .dag import validate_dag, get_ready_nodes, get_approval_nodes, has_failed_nodes, has_running_nodes, all_nodes_successful
from .state import Phase, SystemState

class Orchestrator:
    
    def route(self, state: SystemState) -> Phase:
        """
        Determine what phase the system should be in next.
        This function is deterministic and does not perform work.
        It only examines the current state and determines the next phase.
        """
        
        if(state.error):
            return Phase.FAILED
        if(not state.clarification_checked):
            return Phase.CLARIFY
        if(state.needs_clarification):
            return Phase.CLARIFY
        if(not state.dag):
            return Phase.PLAN

        try:
            validate_dag(state.dag)
        except ValueError as exc:
            state.error = f"Invalid DAG: {exc}"
            return Phase.FAILED
        
        if has_running_nodes(state.dag):
            return Phase.EXECUTE

        if has_failed_nodes(state.dag):
            state.error = "One or more tasks failed."
            return Phase.FAILED

        if all_nodes_successful(state.dag):
            return Phase.DONE

        ready_nodes = get_ready_nodes(state.dag)
        if ready_nodes:
            return Phase.EXECUTE
        
        approval_nodes = get_approval_nodes(state.dag)
        if approval_nodes:
            return Phase.HITL_APPROVAL

        state.error = "The DAG is blocked: no tasks are ready to execute and the workflow is not complete."

        return Phase.FAILED
    
    def step(self, state: SystemState) -> SystemState:
        """
        Advance the state machine by one step.

        The actual work for each phase will be implemented later
        by the corresponding agents/executor.
        """
        
        next_phase = self.route(state)
        
        state.phase = next_phase
        state.iteration_count+=1
        
        return state
        
        