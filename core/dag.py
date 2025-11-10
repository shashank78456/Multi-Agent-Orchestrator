from typing import Dict, List
from .state import NodeStatus, TaskNode
from collections import deque

def validate_dag(dag: Dict[str, TaskNode]) -> List[TaskNode]:
    """
    Validate the DAG.

    Checks:
    1. Dictionary keys match TaskNode IDs.
    2. All dependencies exist.
    3. No node depends on itself.
    4. No duplicate dependencies.
    5. The graph contains no cycles.

    Raises ValueError if the DAG is invalid.
    """
    
    indegree = {node_id: 0 for node_id in dag}
    children = {node_id: [] for node_id in dag}
    
    for node_id, node in dag.items():
        
        if node.id != node_id:
            raise ValueError(f"DAG key '{node_id}' does not match node ID '{node.id}'.")
        
        if len(node.depends_on) != len(set(node.depends_on)):
            raise ValueError(f"Node '{node_id}' contains duplicate dependencies.")
        
        for dependency_id in node.depends_on:
            
            if dependency_id == node_id:
                raise ValueError(f"Node '{node_id}' cannot depend on itself.")

            if dependency_id not in dag:
                raise ValueError(f"Node '{node_id}' depends on missing node '{dependency_id}'.")

            indegree[node_id] += 1
            children[dependency_id].append(node_id)
        
    queue = deque()

    for node_id, degree in indegree.items():
        if degree == 0:
            queue.append(node_id)

    processed = 0

    while queue:

        node_id = queue.popleft()
        processed += 1

        for child_id in children[node_id]:

            indegree[child_id] -= 1

            if indegree[child_id] == 0:
                queue.append(child_id)

    if processed != len(dag):
        raise ValueError("The DAG contains a cycle.")

def get_ready_nodes(dag: Dict[str, TaskNode]) -> List[TaskNode]:
    """
    Return all PENDING nodes whose dependencies have all completed
    successfully.

    A node with no dependencies is immediately ready.
    """
    
    validate_dag(dag)
    
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
    
    validate_dag(dag)

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

def has_running_nodes(dag: Dict[str, TaskNode]) -> bool:
    """
    Return True if at least one node is running
    """
    
    return any(
        node.status == NodeStatus.RUNNING
        for node in dag.values()
    )
    