from core.state import SystemState

class Clarifier:
    
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
            state.clarification_answer = "Could you describe what to do in a bit more detail"
        else:
            state.needs_clarification = False
            state.clarification_question = None
        
        state.clarification_checked = True
        return state
    
    def apply_answer(self, state: SystemState, answer: str) -> SystemState:
        """
        Incorporate the user's clarification into the original query.
        """
        
        answer.strip()
        
        if not state.needs_clarification:
            raise ValueError("The query needs no clarification")

        if not answer:
            raise ValueError("Clarification answer cannot be empty")

        state.clarification_answer = answer
        state.query = {f"{state.query}\nAdditional context: {answer}"}
        state.needs_clarification = False
        state.clarification_question = None
        
        return state
        
        
        