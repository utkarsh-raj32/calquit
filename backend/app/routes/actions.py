"""Endpoints for state-changing actions."""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.auth.models import UserContext
from app.auth.middleware import get_current_user
from app.tools.actions import (
    get_pending_actions, get_executed_actions,
    confirm_action, reject_action
)

router = APIRouter(prefix="/actions", tags=["Actions"])


@router.get("/pending")
async def list_pending_actions(user: UserContext = Depends(get_current_user)):
    """List pending actions. Customers only see their own initiated actions."""
    all_pending = get_pending_actions()
    
    # Filter by user if they are a customer (can only see actions they initiated)
    if user.role.value == "customer":
        filtered = {k: v for k, v in all_pending.items() if v.get("created_by") == user.name}
        return {"actions": list(filtered.values())}
        
    return {"actions": list(all_pending.values())}


@router.post("/{action_id}/confirm")
async def handle_confirm_action(action_id: str, user: UserContext = Depends(get_current_user)):
    """Confirm and execute a pending action."""
    pending = get_pending_actions()
    if action_id not in pending:
        raise HTTPException(status_code=404, detail="Action not found or already processed")
        
    action = pending[action_id]
    
    # Enforce basic authorization - users can generally confirm actions they initiated
    # In a real system, manager approval would be enforced here for high-value credits
    if action.get("needs_manager_approval") and user.role.value != "ops_manager":
        raise HTTPException(status_code=403, detail="Manager approval required for this action")
        
    result = confirm_action(action_id)
    return result


@router.post("/{action_id}/reject")
async def handle_reject_action(action_id: str, user: UserContext = Depends(get_current_user)):
    """Reject a pending action."""
    pending = get_pending_actions()
    if action_id not in pending:
        raise HTTPException(status_code=404, detail="Action not found or already processed")
        
    result = reject_action(action_id)
    return result
