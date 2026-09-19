from core.state import SystemState

class Clarifier:
    
    def __init__(self, llm):
        self.llm = llm
    
    def check(self, state: SystemState) -> SystemState:
        """
        Check whether the user's query needs clarification.
        """
        
        if state.clarification_checked:
            return state
        
        vague_queries = {"", "help", "help me", "tell", "tell me"}
        query = state.query.strip().lower()
        
        if query in vague_queries:
            state.needs_clarification = True
            state.clarification_question = ("Could you describe what you want to accomplish in a little more detail?")
        else:
            state.needs_clarification = False
            state.clarification_question = None
        
        state.clarification_checked = True
        return state
    
    def apply_answer(self, state: SystemState, answer: str) -> SystemState:
        """
        Incorporate the user's clarification into the original query.
        """
        
        answer = answer.strip()
        
        if not state.needs_clarification:
            raise ValueError("The query needs no clarification")

        if not answer:
            raise ValueError("Clarification answer cannot be empty")

        state.clarification_answer = answer
        state.query = (f"{state.query}\nAdditional context: {answer}").strip()
        state.needs_clarification = False
        state.clarification_question = None
        
        return state
        
        
        