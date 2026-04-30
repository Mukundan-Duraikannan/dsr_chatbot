from typing import TypedDict, Optional, List

class AgentState(TypedDict):
    message: str
    role: str
    user_id: int
    intent: Optional[str]
    response: Optional[str]
    rows: Optional[list]
    chat_history: List[str]
    last_employee: Optional[str]   