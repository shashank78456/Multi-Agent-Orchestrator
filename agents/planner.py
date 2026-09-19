import re

from core.dag import validate_dag
from core.state import SystemState, TaskNode

class Planner:
    
    def __init__(self, llm):
        self.llm = llm
    
    def create_plan(self, state: SystemState) -> SystemState:
        """
        Convert the user's query into a task DAG.
        """
        
        if not state.clarification_checked:
            raise ValueError("Clarification has not been completed.")
        if state.needs_clarification:
            raise ValueError("The query still needs clarification.")
        if state.dag:
            raise ValueError("A plan already exists for this query.")
        
        words = set(re.findall(r"[a-z]+", state.query.lower()))
        
        action_words = {"send", "publish", "email", "post", "delete", "purchase", "buy", "submit", "update", "modify"}
        research_words = {"research", "search", "find", "compare", "investigate", "lookup", "explain"}
        
        if(words.intersection(action_words)):
            state.dag = {
                "prepare_action": TaskNode(
                    id="prepare_action",
                    description=f"Prepare the requested action: {state.query}",
                    tool="prepare_action"
                ),
                
                "perform_action": TaskNode(
                    id="perform_action",
                    description=f"Perform the requested action: {state.query}",
                    tool="mock_action",
                    depends_on=["prepare_action"],
                    requires_approval=True
                )
            }
            
        elif(words.intersection(research_words)):
            state.dag = {
                "search_primary": TaskNode(
                    id="search_primary",
                    description=f"Find primary information about: {state.query}",
                    tool="mock_search"
                ),

                "search_secondary": TaskNode(
                    id="search_secondary",
                    description=f"Find additional information about: {state.query}",
                    tool="mock_search"
                ),

                "summarize": TaskNode(
                    id="summarize",
                    description="Summarize the gathered information.",
                    tool="summarize",
                    depends_on=["search_primary", "search_secondary",]
                )
            }
            
        else:
            state.dag = {
                "respond": TaskNode(
                    id="respond",
                    description=f"Process the user's request: {state.query}",
                    tool="echo"
                )
            }
        
        validate_dag(state.dag)
        
        return state