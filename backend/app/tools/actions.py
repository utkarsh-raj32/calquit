"""Tool 3: State-Changing Actions.

Performs actions like escalations, ticket updates, follow-up tasks, and order
cancellations. All actions require explicit user confirmation before execution.
"""

from langchain_core.tools import tool
from typing import Optional
from datetime import datetime
import json
import uuid

from app.auth.models import UserContext, UserRole

_current_user: Optional[UserContext] = None

# In-memory store for pending and executed actions
_pending_actions: dict[str, dict] = {}
_executed_actions: list[dict] = []


def set_user_context(user: UserContext):
    global _current_user
    _current_user = user


def get_pending_actions() -> dict:
    return _pending_actions


def get_executed_actions() -> list:
    return _executed_actions


def confirm_action(action_id: str) -> dict:
    """Confirm and execute a pending action."""
    if action_id not in _pending_actions:
        return {"error": f"Action {action_id} not found or already processed."}

    action = _pending_actions.pop(action_id)
    action["status"] = "executed"
    action["executed_at"] = datetime.utcnow().isoformat()
    _executed_actions.append(action)
    return {"success": True, "action": action}


def reject_action(action_id: str) -> dict:
    """Reject a pending action."""
    if action_id not in _pending_actions:
        return {"error": f"Action {action_id} not found or already processed."}

    action = _pending_actions.pop(action_id)
    action["status"] = "rejected"
    return {"success": True, "action": action}


@tool
def create_escalation(ticket_id: str, reason: str, severity: str = "P2") -> str:
    """Create an escalation for a support ticket. Requires user confirmation before execution.

    Use when a ticket needs urgent attention, SLA is breached, or the issue
    requires higher-level intervention.

    Args:
        ticket_id: The ticket to escalate (e.g., 'TKT-501').
        reason: Why this ticket needs escalation.
        severity: Escalation severity - 'P1', 'P2', or 'P3'.
    """
    if _current_user is None:
        return "Error: No user context set."

    action_id = f"act_{uuid.uuid4().hex[:8]}"
    action = {
        "action_id": action_id,
        "action_type": "escalation",
        "status": "pending_confirmation",
        "ticket_id": ticket_id,
        "severity": severity,
        "reason": reason,
        "created_by": _current_user.name,
        "created_at": datetime.utcnow().isoformat(),
    }
    _pending_actions[action_id] = action

    return json.dumps({
        "message": f"⚠️ CONFIRMATION REQUIRED: Escalation prepared for {ticket_id}.",
        "action_id": action_id,
        "action_type": "escalation",
        "details": {
            "ticket_id": ticket_id,
            "severity": severity,
            "reason": reason,
        },
        "instruction": "This action requires user confirmation before it will be executed. Please confirm or cancel.",
    }, indent=2)


@tool
def update_ticket(ticket_id: str, new_status: Optional[str] = None, notes: Optional[str] = None) -> str:
    """Update a support ticket's status or add notes. Requires user confirmation.

    Args:
        ticket_id: The ticket to update (e.g., 'TKT-501').
        new_status: New status to set (e.g., 'in_progress', 'resolved', 'closed').
        notes: Notes to add to the ticket.
    """
    if _current_user is None:
        return "Error: No user context set."

    if _current_user.role == UserRole.CUSTOMER:
        return "Error: Customers cannot directly update tickets. Please contact support."

    action_id = f"act_{uuid.uuid4().hex[:8]}"
    action = {
        "action_id": action_id,
        "action_type": "update_ticket",
        "status": "pending_confirmation",
        "ticket_id": ticket_id,
        "new_status": new_status,
        "notes": notes,
        "created_by": _current_user.name,
        "created_at": datetime.utcnow().isoformat(),
    }
    _pending_actions[action_id] = action

    return json.dumps({
        "message": f"⚠️ CONFIRMATION REQUIRED: Ticket update prepared for {ticket_id}.",
        "action_id": action_id,
        "action_type": "update_ticket",
        "details": {
            "ticket_id": ticket_id,
            "new_status": new_status,
            "notes": notes,
        },
        "instruction": "This action requires user confirmation before it will be executed.",
    }, indent=2)


@tool
def create_followup_task(ticket_id: str, description: str, assignee: Optional[str] = None) -> str:
    """Create a follow-up task for a support ticket. Requires user confirmation.

    Args:
        ticket_id: The related ticket ID.
        description: Description of the follow-up task.
        assignee: Optional person to assign the task to.
    """
    if _current_user is None:
        return "Error: No user context set."

    if _current_user.role == UserRole.CUSTOMER:
        return "Error: Customers cannot create tasks."

    action_id = f"act_{uuid.uuid4().hex[:8]}"
    action = {
        "action_id": action_id,
        "action_type": "followup_task",
        "status": "pending_confirmation",
        "ticket_id": ticket_id,
        "description": description,
        "assignee": assignee or "Unassigned",
        "created_by": _current_user.name,
        "created_at": datetime.utcnow().isoformat(),
    }
    _pending_actions[action_id] = action

    return json.dumps({
        "message": f"⚠️ CONFIRMATION REQUIRED: Follow-up task prepared for {ticket_id}.",
        "action_id": action_id,
        "action_type": "followup_task",
        "details": {
            "ticket_id": ticket_id,
            "description": description,
            "assignee": assignee or "Unassigned",
        },
        "instruction": "This action requires user confirmation before it will be executed.",
    }, indent=2)


@tool
def request_order_cancellation(order_id: str, reason: str) -> str:
    """Request cancellation of an order. Requires user confirmation.

    The cancellation fee (if any) will be calculated based on the order status,
    time since booking, and customer agreement terms.

    Args:
        order_id: The order to cancel (e.g., 'ORD-1001').
        reason: Reason for cancellation.
    """
    if _current_user is None:
        return "Error: No user context set."

    from app.data.structured import calculate_cancellation_eligibility
    eligibility = calculate_cancellation_eligibility(order_id, _current_user)

    if not eligibility.get("eligible"):
        return json.dumps({
            "message": f"❌ Cannot cancel order {order_id}.",
            "reason": eligibility.get("reason", "Unknown"),
            "source": eligibility.get("source", "Unknown"),
        }, indent=2)

    action_id = f"act_{uuid.uuid4().hex[:8]}"
    action = {
        "action_id": action_id,
        "action_type": "cancel_order",
        "status": "pending_confirmation",
        "order_id": order_id,
        "reason": reason,
        "fee": eligibility.get("fee", 0),
        "eligibility_details": eligibility,
        "created_by": _current_user.name,
        "created_at": datetime.utcnow().isoformat(),
    }
    _pending_actions[action_id] = action

    return json.dumps({
        "message": f"⚠️ CONFIRMATION REQUIRED: Order cancellation prepared for {order_id}.",
        "action_id": action_id,
        "action_type": "cancel_order",
        "details": {
            "order_id": order_id,
            "reason": reason,
            "fee": eligibility.get("fee", 0),
            "fee_explanation": eligibility.get("reason", ""),
            "source": eligibility.get("source", ""),
        },
        "instruction": "This action requires user confirmation before it will be executed.",
    }, indent=2)


@tool
def request_service_credit(order_id: str, reason: str) -> str:
    """Request a service credit for a failed or late pickup. Requires user confirmation.

    Args:
        order_id: The order to credit (e.g., 'ORD-2002').
        reason: Reason for the credit request.
    """
    if _current_user is None:
        return "Error: No user context set."

    from app.data.structured import calculate_service_credit_eligibility
    eligibility = calculate_service_credit_eligibility(order_id, _current_user)

    if not eligibility.get("eligible"):
        return json.dumps({
            "message": f"❌ Service credit not applicable for order {order_id}.",
            "reason": eligibility.get("reason", "Unknown"),
            "source": eligibility.get("source", "Unknown"),
        }, indent=2)

    credit_amount = eligibility.get("credit_amount", 0)
    needs_approval = credit_amount > 1000

    action_id = f"act_{uuid.uuid4().hex[:8]}"
    action = {
        "action_id": action_id,
        "action_type": "service_credit",
        "status": "pending_confirmation",
        "order_id": order_id,
        "reason": reason,
        "credit_amount": credit_amount,
        "needs_manager_approval": needs_approval,
        "eligibility_details": eligibility,
        "created_by": _current_user.name,
        "created_at": datetime.utcnow().isoformat(),
    }
    _pending_actions[action_id] = action

    approval_note = " ⚠️ This credit exceeds INR 1,000 and requires manager approval." if needs_approval else ""

    return json.dumps({
        "message": f"⚠️ CONFIRMATION REQUIRED: Service credit of INR {credit_amount:.0f} prepared for {order_id}.{approval_note}",
        "action_id": action_id,
        "action_type": "service_credit",
        "details": {
            "order_id": order_id,
            "reason": reason,
            "credit_amount": credit_amount,
            "needs_manager_approval": needs_approval,
            "explanation": eligibility.get("reason", ""),
            "source": eligibility.get("source", ""),
        },
        "instruction": "This action requires user confirmation before it will be executed.",
    }, indent=2)
