from .dag import get_ready_nodes, get_approval_nodes, has_failed_nodes, all_nodes_successful
from .state import Phase, SystemState

class Orchestrator:
    
    def route(self, state: SystemState) -> Phase:
        """
        Determine what phase the system should be in next.
        This function is deterministic and does not perform work.
        """
        
        if(state.error):
            return Phase.FAILED
        if(state.needs_clarification):
            return Phase.CLARIFY
        if(not state.dag):
            return Phase.PLAN
        
        approval_nodes = get_approval_nodes(state.dag)
        if(approval_nodes):
            return Phase.HITL_APPROVAl
        
        ready_nodes = get_ready_nodes(state.dag)
        if(ready_nodes):
            return Phase.EXECUTE
        
        if(all_nodes_successful(state.dag)):
            return Phase.DONE
        
        if(has_failed_nodes(state.dag)):
            return Phase.FAILED
        
        state.error = "No executable nodes exist and DAG is not complete"
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
        
        