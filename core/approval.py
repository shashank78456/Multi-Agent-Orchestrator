from typing import List

from core.dag import get_approval_nodes
from core.state import NodeStatus, SystemState, TaskNode

class ApprovalManager:
    
    def get_pending_approvals(self, state: SystemState) -> List[TaskNode]:
        """
        Return tasks currently waiting for human approval.
        """
        
        return get_approval_nodes(state.dag)
    
    def approve_task(self, state: SystemState, node_id: str) -> TaskNode:
        """
        Approve a task so that it can be executed.
        """
        
        pending_nodes = self.get_pending_approvals(state)
        for node in pending_nodes:
            if node.id == node_id:
                node.approved = True
                return node

        raise ValueError(f"Task '{node_id}' is not currently awaiting approval.")
    
    def reject_task(self, state: SystemState, node_id: str) -> TaskNode:
        """
        Reject a task and fail the workflow.
        """
        
        pending_nodes = self.get_pending_approvals(state)
        for node in pending_nodes:
            if node.id == node_id:
                node.status = NodeStatus.FAILED
                node.error = "Rejected by user."
                state.error = (f"Task '{node_id}' was rejected by the user.")
                return node

        raise ValueError(f"Task '{node_id}' is not currently awaiting approval.")
    
    