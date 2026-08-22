"""LangGraph orchestrator for the ParcelPilot AI."""

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Literal

from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.auth.models import UserRole
from app.agent.state import AgentState
from app.agent.prompts import CUSTOMER_SYSTEM_PROMPT, INTERNAL_SYSTEM_PROMPT

# Tools
from app.tools.document_search import document_search, set_user_context as set_doc_user
from app.tools.data_lookup import (
    lookup_order, lookup_account, lookup_tickets, list_orders,
    calculate_cancellation, calculate_service_credit, check_ticket_sla,
    set_user_context as set_data_user
)
from app.tools.actions import (
    create_escalation, update_ticket, create_followup_task,
    request_order_cancellation, request_service_credit,
    set_user_context as set_action_user
)

# Bind all tools
TOOLS = [
    document_search,
    lookup_order, lookup_account, lookup_tickets, list_orders,
    calculate_cancellation, calculate_service_credit, check_ticket_sla,
    create_escalation, update_ticket, create_followup_task,
    request_order_cancellation, request_service_credit
]

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GEMINI_API_KEY,
    temperature=0.0,  # Low temperature for factual, reliable answers
    max_output_tokens=2048,
)
llm_with_tools = llm.bind_tools(TOOLS)


def _set_tool_contexts(user):
    """Set the user context for all tools before executing."""
    set_doc_user(user)
    set_data_user(user)
    set_action_user(user)


def agent_node(state: AgentState):
    """The main reasoning node that decides what to do next."""
    messages = list(state["messages"])
    user = state["user"]
    
    # Determine the right system prompt based on user role
    sys_prompt = CUSTOMER_SYSTEM_PROMPT if user.role == UserRole.CUSTOMER else INTERNAL_SYSTEM_PROMPT
    
    # Ensure the first message is the system prompt
    if not messages or not isinstance(messages[0], SystemMessage):
        messages.insert(0, SystemMessage(content=sys_prompt))
    else:
        # Update system prompt if it changed (unlikely in a single run, but good practice)
        messages[0] = SystemMessage(content=sys_prompt)
        
    # Inject user context into tools
    _set_tool_contexts(user)

    # Invoke LLM
    response = llm_with_tools.invoke(messages)
    
    return {"messages": [response]}


def route_after_agent(state: AgentState) -> Literal["tools", "__end__"]:
    """Determine whether to call a tool or end the conversation."""
    last_message = state["messages"][-1]
    
    # If the LLM made a tool call, route to tools
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    # Otherwise, end
    return "__end__"


# Build the graph
workflow = StateGraph(AgentState)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(TOOLS))

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    route_after_agent,
)
workflow.add_edge("tools", "agent")

# Compile the graph
app_graph = workflow.compile()
