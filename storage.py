import json
import os
import tempfile
from pathlib import Path

from core.dag import validate_dag
from core.state import SystemState

def save_state(state: SystemState, filename: str="state.json") -> None:
    """
    Persist the current system state to a JSON file.

    Uses a temporary file and os.replace() to avoid leaving
    a partially written state file if saving is interrupted.
    """
    
    validate_dag(state.dag)
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as file:
            temporary_path = Path(file.name)

            json.dump(state.model_dump(mode="json"), file, indent=4, ensure_ascii=False)

            file.flush()
            os.fsync(file.fileno())
            
        os.replace(temporary_path, path)
        
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
            
def load_state(filename: str = "state.json") -> SystemState:
    """
    Load a previously saved system state.

    Reconstructs the Pydantic models and validates the DAG.
    """
    
    path = Path(filename)

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    state = SystemState.model_validate(data)
    
    validate_dag(state.dag)

    return state
    
    