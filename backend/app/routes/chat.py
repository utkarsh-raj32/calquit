"""Chat endpoints with SSE streaming."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json
import asyncio

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from app.auth.models import UserContext
from app.auth.middleware import get_current_user
from app.agent.graph import app_graph
from app.agent.state import AgentState

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatMessage(BaseModel):
    role: str  # 'user', 'assistant', 'tool'
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


def convert_messages(input_messages: List[ChatMessage]):
    """Convert frontend message format to LangChain format."""
    lc_messages = []
    for msg in input_messages:
        if msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            # Very simplified handling of assistant messages
            # For a production app, we'd need to correctly restore tool_calls
            lc_messages.append(AIMessage(content=msg.content))
        elif msg.role == "tool":
            lc_messages.append(ToolMessage(
                content=msg.content,
                name=msg.name or "unknown",
                tool_call_id=msg.tool_call_id or "unknown"
            ))
    return lc_messages


async def stream_agent_events(messages: list, user: UserContext):
    """Generator for SSE streaming of agent execution."""
    
    # Initialize state
    state: AgentState = {
        "messages": messages,
        "user": user,
    }
    
    try:
        # We use astream_events to get granular token and tool events
        async for event in app_graph.astream_events(state, version="v2"):
            kind = event["event"]
            
            # Tool usage started
            if kind == "on_tool_start":
                data = json.dumps({
                    "type": "tool_start",
                    "tool": event["name"],
                    "input": event["data"].get("input", {})
                })
                yield f"data: {data}\n\n"
                
            # Tool usage ended
            elif kind == "on_tool_end":
                data = json.dumps({
                    "type": "tool_end",
                    "tool": event["name"],
                    "output": str(event["data"].get("output", ""))
                })
                yield f"data: {data}\n\n"
                
            # LLM streaming tokens
            elif kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                content = chunk.content
                text_content = ""
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and "text" in item:
                            text_content += item["text"]
                        elif isinstance(item, str):
                            text_content += item
                else:
                    text_content = str(content) if content else ""
                    
                if text_content:
                    data = json.dumps({
                        "type": "token",
                        "content": text_content
                    })
                    yield f"data: {data}\n\n"
                    
            # Handle potential rate limits gently (sleep slightly)
            await asyncio.sleep(0.01)
            
    except Exception as e:
        error_msg = json.dumps({
            "type": "error",
            "content": f"An error occurred: {str(e)}"
        })
        yield f"data: {error_msg}\n\n"
        
    # Send done signal
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    user: UserContext = Depends(get_current_user)
):
    """Stream agent response using Server-Sent Events (SSE)."""
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages cannot be empty")
        
    lc_messages = convert_messages(request.messages)
    
    return StreamingResponse(
        stream_agent_events(lc_messages, user),
        media_type="text/event-stream"
    )
