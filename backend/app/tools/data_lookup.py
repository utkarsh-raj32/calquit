"""Tool 2: Structured Data Lookup and Calculation.

Queries ParcelPilot's operational data (accounts, orders, tickets) with
access control, and performs business calculations.
"""

from langchain_core.tools import tool
from typing import Optional
import json

from app.data.structured import (
    get_account, get_all_accounts, get_order, get_orders_for_account,
    get_ticket, get_tickets_for_account, get_all_tickets, get_all_orders,
    calculate_cancellation_eligibility, calculate_service_credit_eligibility,
    check_sla_status,
)
from app.auth.models import UserContext

_current_user: Optional[UserContext] = None


def set_user_context(user: UserContext):
    global _current_user
    _current_user = user


def _json(data) -> str:
    """Convert data to formatted JSON string."""
    return json.dumps(data, indent=2, default=str)


@tool
def lookup_order(order_id: str) -> str:
    """Look up details of a specific order by its order ID (e.g., ORD-1001).

    Returns order details including status, carrier, booking time, pickup window,
    shipment fee, and fault information. Access is scoped to the user's account
    for customer users.

    Args:
        order_id: The order ID to look up (e.g., 'ORD-1001').
    """
    if _current_user is None:
        return "Error: No user context set."
    result = get_order(order_id, _current_user)
    if result is None:
        return f"Order {order_id} not found or you do not have access to view it."
    return f"Order details for {order_id}:\n{_json(result)}"


@tool
def lookup_account(account_id: str) -> str:
    """Look up details of a specific account by its account ID (e.g., ACCT-001).

    Returns account name, plan, status, CSM, and whether a custom agreement exists.

    Args:
        account_id: The account ID to look up (e.g., 'ACCT-001').
    """
    if _current_user is None:
        return "Error: No user context set."
    result = get_account(account_id, _current_user)
    if result is None:
        return f"Account {account_id} not found or you do not have access."
    return f"Account details for {account_id}:\n{_json(result)}"


@tool
def lookup_tickets(account_id: Optional[str] = None, status: Optional[str] = None) -> str:
    """Look up support tickets, optionally filtered by account and/or status.

    Args:
        account_id: Optional account ID to filter tickets (e.g., 'ACCT-001').
        status: Optional status filter - 'open' or 'closed'.
    """
    if _current_user is None:
        return "Error: No user context set."
    if account_id:
        results = get_tickets_for_account(account_id, _current_user, status=status)
    else:
        results = get_all_tickets(_current_user, status=status)
    if not results:
        return "No tickets found matching your criteria."
    return f"Found {len(results)} ticket(s):\n{_json(results)}"


@tool
def calculate_cancellation(order_id: str) -> str:
    """Calculate whether an order can be cancelled and the applicable cancellation fee.

    This accounts for the order's current status, time since booking, and any
    customer-specific agreement overrides. Uses the source precedence:
    signed customer agreement > current Cancellation SOP > default rules.

    Args:
        order_id: The order ID to evaluate (e.g., 'ORD-1001').
    """
    if _current_user is None:
        return "Error: No user context set."
    result = calculate_cancellation_eligibility(order_id, _current_user)
    return f"Cancellation analysis for {order_id}:\n{_json(result)}"


@tool
def calculate_service_credit(order_id: str) -> str:
    """Calculate service credit eligibility for a failed or late pickup.

    Evaluates carrier fault, customer fault, pickup delay against the applicable
    threshold, and calculates the credit amount. Uses the source precedence:
    signed customer agreement > current Service Credit SOP > default rules.

    Args:
        order_id: The order ID to evaluate (e.g., 'ORD-2002').
    """
    if _current_user is None:
        return "Error: No user context set."
    result = calculate_service_credit_eligibility(order_id, _current_user)
    return f"Service credit analysis for {order_id}:\n{_json(result)}"


@tool
def check_ticket_sla(ticket_id: str) -> str:
    """Check if a support ticket's response SLA target has been met or breached.

    Determines the ticket severity, applicable SLA target (from customer agreement
    or default support policy), and whether the target has been exceeded.

    Args:
        ticket_id: The ticket ID to check (e.g., 'TKT-501').
    """
    if _current_user is None:
        return "Error: No user context set."
    result = check_sla_status(ticket_id, _current_user)
    return f"SLA status for {ticket_id}:\n{_json(result)}"


@tool
def list_orders(account_id: Optional[str] = None) -> str:
    """List all orders, optionally filtered by account.

    Args:
        account_id: Optional account ID to filter orders.
    """
    if _current_user is None:
        return "Error: No user context set."
    if account_id:
        results = get_orders_for_account(account_id, _current_user)
    else:
        results = get_all_orders(_current_user)
    if not results:
        return "No orders found."
    return f"Found {len(results)} order(s):\n{_json(results)}"
