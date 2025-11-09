from typing import Dict, List
from .state import NodeStatus, TaskNode

def get_ready_nodes(dag: Dict[str, TaskNode]) -> List[TaskNode]:
    """
    Return all PENDING nodes whose dependencies have all completed
    successfully.

    A node with no dependencies is immediately ready.
    """
    
    ready_nodes = []
    for node in dag.values():
        if(node.status != NodeStatus.PENDING):
            continue
        if(node.requires_approval and not node.approved):
            continue
        
        dependencies_ready = all(dag[dependency_id].status == NodeStatus.SUCCESS for dependency_id in node.depends_on)
        if(dependencies_ready):
            ready_nodes.append(node)
    
    return ready_nodes

def get_approval_nodes(dag: Dict[str, TaskNode]) -> List[TaskNode]:
    """
    Return PENDING nodes that:
    - have all dependencies completed successfully
    - require human approval
    - have not yet been approved
    """

    approval_nodes = []

    for node in dag.values():

        if node.status != NodeStatus.PENDING:
            continue

        if not node.requires_approval:
            continue

        if node.approved:
            continue

        dependencies_ready = all(
            dag[dependency_id].status == NodeStatus.SUCCESS
            for dependency_id in node.depends_on
        )

        if dependencies_ready:
            approval_nodes.append(node)

    return approval_nodes

def all_nodes_completed(dag : Dict[str, TaskNode]) -> bool:
    """
    Return True when every node has reached SUCCESS or FAILED.
    """
    
    if not dag:
        return False
    
    return all(node.status in {NodeStatus.SUCCESS, NodeStatus.FAILED} for node in dag.values())

def all_nodes_successful(dag: Dict[str, TaskNode]) -> bool:
    """
    Return True when every node has completed successfully.
    """

    if not dag:
        return False

    return all(
        node.status == NodeStatus.SUCCESS
        for node in dag.values()
    )
    
def has_failed_nodes(dag: Dict[str, TaskNode]) -> bool:
    """
    Return True if at least one node has failed.
    """

    return any(
        node.status == NodeStatus.FAILED
        for node in dag.values()
    )

