"""State definition for the LangGraph agent."""

from typing import Annotated, Sequence, TypedDict, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from app.auth.models import UserContext

class AgentState(TypedDict):
    """State for the ParcelPilot support agent."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user: UserContext
    # We could add more state here later if needed, like extracted entities or routing flags
