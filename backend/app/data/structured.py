"""Structured data access layer for ParcelPilot operational data.

Loads the Excel workbook into Pandas DataFrames and provides
access-controlled query functions.
"""

import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Optional
from pathlib import Path

from app.config import DATA_DIR, DATASET_SNAPSHOT
from app.auth.models import UserContext, UserRole

# IST timezone
IST = timezone(timedelta(hours=5, minutes=30))

# Dataset snapshot as datetime
SNAPSHOT_DT = datetime.fromisoformat(DATASET_SNAPSHOT).replace(tzinfo=None)

# ---------------------------------------------------------------------------
# Load data on import
# ---------------------------------------------------------------------------
_xlsx_path = DATA_DIR / "ParcelPilot_Assessment_Data.xlsx"

df_accounts: pd.DataFrame = pd.DataFrame()
df_orders: pd.DataFrame = pd.DataFrame()
df_tickets: pd.DataFrame = pd.DataFrame()


def load_structured_data():
    """Load Excel sheets into module-level DataFrames."""
    global df_accounts, df_orders, df_tickets

    df_accounts = pd.read_excel(_xlsx_path, sheet_name="accounts")
    df_orders = pd.read_excel(_xlsx_path, sheet_name="orders")
    df_tickets = pd.read_excel(_xlsx_path, sheet_name="tickets")

    # Normalize datetime columns
    for col in ["booked_at", "pickup_window_start", "pickup_window_end",
                 "pickup_actual_at", "cancellation_requested_at"]:
        if col in df_orders.columns:
            df_orders[col] = pd.to_datetime(df_orders[col], errors="coerce")

    for col in ["created_at", "last_customer_message_at"]:
        if col in df_tickets.columns:
            df_tickets[col] = pd.to_datetime(df_tickets[col], errors="coerce")


# ---------------------------------------------------------------------------
# Access-controlled query functions
# ---------------------------------------------------------------------------

def _scope_account(df: pd.DataFrame, user: UserContext) -> pd.DataFrame:
    """Filter DataFrame to user's account if they are a customer."""
    if user.role == UserRole.CUSTOMER and user.account_id:
        return df[df["account_id"] == user.account_id]
    return df


def get_account(account_id: str, user: UserContext) -> Optional[dict]:
    """Get account details (access controlled)."""
    df = _scope_account(df_accounts, user)
    row = df[df["account_id"] == account_id]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


def get_all_accounts(user: UserContext) -> list[dict]:
    """Get all accessible accounts."""
    df = _scope_account(df_accounts, user)
    return df.to_dict(orient="records")


def get_order(order_id: str, user: UserContext) -> Optional[dict]:
    """Get order details (access controlled)."""
    df = _scope_account(df_orders, user)
    row = df[df["order_id"] == order_id]
    if row.empty:
        return None
    record = row.iloc[0].to_dict()
    # Convert Timestamps to strings for JSON serialization
    for k, v in record.items():
        if isinstance(v, pd.Timestamp):
            record[k] = v.isoformat() if not pd.isna(v) else None
        elif pd.isna(v):
            record[k] = None
    return record


def get_orders_for_account(account_id: str, user: UserContext) -> list[dict]:
    """Get all orders for an account (access controlled)."""
    df = _scope_account(df_orders, user)
    filtered = df[df["account_id"] == account_id]
    records = filtered.to_dict(orient="records")
    for record in records:
        for k, v in record.items():
            if isinstance(v, pd.Timestamp):
                record[k] = v.isoformat() if not pd.isna(v) else None
            elif pd.isna(v):
                record[k] = None
    return records


def get_ticket(ticket_id: str, user: UserContext) -> Optional[dict]:
    """Get ticket details (access controlled)."""
    df = _scope_account(df_tickets, user)
    row = df[df["ticket_id"] == ticket_id]
    if row.empty:
        return None
    record = row.iloc[0].to_dict()
    for k, v in record.items():
        if isinstance(v, pd.Timestamp):
            record[k] = v.isoformat() if not pd.isna(v) else None
        elif pd.isna(v):
            record[k] = None
    return record


def get_tickets_for_account(
    account_id: str,
    user: UserContext,
    status: Optional[str] = None,
) -> list[dict]:
    """Get tickets for an account, optionally filtered by status."""
    df = _scope_account(df_tickets, user)
    filtered = df[df["account_id"] == account_id]
    if status:
        filtered = filtered[filtered["status"] == status]
    records = filtered.to_dict(orient="records")
    for record in records:
        for k, v in record.items():
            if isinstance(v, pd.Timestamp):
                record[k] = v.isoformat() if not pd.isna(v) else None
            elif pd.isna(v):
                record[k] = None
    return records


def get_all_tickets(user: UserContext, status: Optional[str] = None) -> list[dict]:
    """Get all accessible tickets."""
    df = _scope_account(df_tickets, user)
    if status:
        df = df[df["status"] == status]
    records = df.to_dict(orient="records")
    for record in records:
        for k, v in record.items():
            if isinstance(v, pd.Timestamp):
                record[k] = v.isoformat() if not pd.isna(v) else None
            elif pd.isna(v):
                record[k] = None
    return records


def get_all_orders(user: UserContext) -> list[dict]:
    """Get all accessible orders."""
    df = _scope_account(df_orders, user)
    records = df.to_dict(orient="records")
    for record in records:
        for k, v in record.items():
            if isinstance(v, pd.Timestamp):
                record[k] = v.isoformat() if not pd.isna(v) else None
            elif pd.isna(v):
                record[k] = None
    return records


def calculate_cancellation_eligibility(order_id: str, user: UserContext) -> dict:
    """Calculate whether an order can be cancelled and the applicable fee.

    Uses the source precedence: customer agreement > current SOP > default.
    """
    order = get_order(order_id, user)
    if not order:
        return {"eligible": False, "reason": "Order not found or access denied."}

    status = order["status"]
    account_id = order["account_id"]
    account = get_account(account_id, user) if user.role != UserRole.CUSTOMER else get_account(user.account_id, user)

    result = {
        "order_id": order_id,
        "status": status,
        "account_id": account_id,
        "account_name": account["account_name"] if account else "Unknown",
    }

    # Status-based rules (from Cancellation SOP v4)
    if status == "DRAFT":
        result.update({"eligible": True, "fee": 0, "reason": "DRAFT orders can be cancelled with no fee.", "source": "Cancellation SOP v4"})
        return result

    if status == "DELIVERED":
        result.update({"eligible": False, "fee": None, "reason": "DELIVERED orders cannot be cancelled.", "source": "Cancellation SOP v4"})
        return result

    if status == "PICKED_UP":
        result.update({"eligible": False, "fee": None, "reason": "PICKED_UP orders cannot be cancelled. Use the return-to-origin workflow instead.", "source": "Cancellation SOP v4"})
        return result

    if status == "BOOKED":
        booked_at = pd.to_datetime(order["booked_at"])
        cancel_at = pd.to_datetime(order.get("cancellation_requested_at")) if order.get("cancellation_requested_at") else SNAPSHOT_DT

        minutes_since_booking = (cancel_at - booked_at).total_seconds() / 60

        # Check for customer-specific agreement overrides
        if account_id == "ACCT-001":
            # Northstar: "may cancel any BOOKED shipment before pickup with no cancellation fee"
            result.update({
                "eligible": True,
                "fee": 0,
                "reason": f"Northstar's Enterprise Agreement allows cancellation of any BOOKED shipment before pickup with no fee. Time since booking: {minutes_since_booking:.0f} minutes.",
                "source": "Northstar Logistics Enterprise Agreement (overrides SOP)",
                "source_note": "Customer agreement takes precedence over default SOP."
            })
            return result

        # Default SOP rules for BOOKED
        if minutes_since_booking <= 30:
            result.update({
                "eligible": True,
                "fee": 0,
                "reason": f"Cancellation requested within 30 minutes of booking ({minutes_since_booking:.0f} min). No fee applies.",
                "source": "Cancellation SOP v4"
            })
        else:
            result.update({
                "eligible": True,
                "fee": 250,
                "reason": f"Cancellation requested {minutes_since_booking:.0f} minutes after booking (>30 min). Standard INR 250 cancellation fee applies.",
                "source": "Cancellation SOP v4"
            })

        return result

    result.update({"eligible": False, "reason": f"Unknown order status: {status}"})
    return result


def calculate_service_credit_eligibility(order_id: str, user: UserContext) -> dict:
    """Calculate service credit eligibility for a failed/late pickup.

    Uses source precedence: customer agreement > current SOP > default.
    """
    order = get_order(order_id, user)
    if not order:
        return {"eligible": False, "reason": "Order not found or access denied."}

    account_id = order["account_id"]
    account = get_account(account_id, user) if user.role != UserRole.CUSTOMER else get_account(user.account_id, user)
    shipment_fee = order.get("shipment_fee_inr", 0) or 0

    result = {
        "order_id": order_id,
        "account_id": account_id,
        "account_name": account["account_name"] if account else "Unknown",
        "carrier_fault": order.get("carrier_fault"),
        "customer_fault": order.get("customer_fault"),
    }

    # Check carrier fault
    if not order.get("carrier_fault"):
        result.update({
            "eligible": False,
            "credit_amount": 0,
            "reason": "Carrier fault has not been confirmed. Service credit requires carrier fault.",
            "source": "Cancellation & Service Credit SOP v4",
        })
        return result

    if order.get("customer_fault"):
        result.update({
            "eligible": False,
            "credit_amount": 0,
            "reason": "Customer-caused issue identified. Service credit is not applicable when customer is at fault.",
            "source": "Cancellation & Service Credit SOP v4",
        })
        return result

    # Calculate delay
    pickup_window_end = pd.to_datetime(order.get("pickup_window_end"))
    pickup_actual = pd.to_datetime(order.get("pickup_actual_at")) if order.get("pickup_actual_at") else SNAPSHOT_DT

    if pickup_window_end and pickup_actual:
        delay_hours = (pickup_actual - pickup_window_end).total_seconds() / 3600
    else:
        delay_hours = None

    result["delay_hours"] = round(delay_hours, 2) if delay_hours is not None else None

    # Customer-specific thresholds
    if account_id == "ACCT-002":
        # LumenWorks: 4-hour threshold, fixed INR 300 credit
        threshold_hours = 4
        if delay_hours is not None and delay_hours >= threshold_hours:
            result.update({
                "eligible": True,
                "credit_amount": 300,
                "reason": f"Pickup was {delay_hours:.1f} hours late (>= {threshold_hours}h LumenWorks threshold). Carrier fault confirmed. Fixed INR 300 credit per LumenWorks agreement.",
                "source": "LumenWorks Service Agreement (overrides default SOP)",
            })
        else:
            result.update({
                "eligible": False,
                "credit_amount": 0,
                "reason": f"Pickup was {delay_hours:.1f} hours late, but LumenWorks' agreement requires >= {threshold_hours} hours delay. Threshold not met.",
                "source": "LumenWorks Service Agreement (overrides default SOP)",
            })
        return result

    # Default SOP: 2-hour threshold, lower of INR 500 or 10% of shipment fee
    threshold_hours = 2
    if delay_hours is not None and delay_hours >= threshold_hours:
        default_credit = min(500, shipment_fee * 0.10)
        result.update({
            "eligible": True,
            "credit_amount": default_credit,
            "reason": f"Pickup was {delay_hours:.1f} hours late (>= {threshold_hours}h default threshold). Carrier fault confirmed. Credit: lower of INR 500 or 10% of INR {shipment_fee} fee = INR {default_credit:.0f}.",
            "source": "Cancellation & Service Credit SOP v4",
        })
    else:
        delay_str = f"{delay_hours:.1f} hours" if delay_hours is not None else "unknown"
        result.update({
            "eligible": False,
            "credit_amount": 0,
            "reason": f"Pickup delay is {delay_str}, which is below the {threshold_hours}-hour default threshold.",
            "source": "Cancellation & Service Credit SOP v4",
        })

    # Check Northstar cap
    if account_id == "ACCT-001" and result.get("eligible"):
        result["note"] = "Northstar has a monthly aggregate service credit cap of INR 5,000 per their Enterprise Agreement."

    return result


def check_sla_status(ticket_id: str, user: UserContext) -> dict:
    """Check if a ticket's response SLA has been met or breached."""
    ticket = get_ticket(ticket_id, user)
    if not ticket:
        return {"status": "error", "reason": "Ticket not found or access denied."}

    account = get_account(ticket["account_id"], user) if user.role != UserRole.CUSTOMER else get_account(user.account_id, user)
    if not account:
        return {"status": "error", "reason": "Account not found."}

    plan = account.get("plan", "Standard")
    created_at = pd.to_datetime(ticket["created_at"])

    # Determine severity from ticket content (simplified heuristic)
    subject = (ticket.get("subject") or "").lower()
    description = (ticket.get("description") or "").lower()

    if any(kw in subject + description for kw in ["outage", "all shipment", "http 500", "api key exposure", "credential", "security"]):
        severity = "P1"
    elif any(kw in subject + description for kw in ["bulk upload fail", "major", "degraded"]):
        severity = "P2"
    else:
        severity = "P3"

    # SLA targets (from Support Policy v3 + customer agreements)
    sla_targets = {
        # Default from Support Policy v3
        "Enterprise": {"P1": 30, "P2": 120, "P3": 480},       # minutes
        "Growth":     {"P1": 120, "P2": 240, "P3": 960},
        "Standard":   {"P1": 240, "P2": 480, "P3": 960},
    }

    # Customer-specific overrides
    account_id = ticket["account_id"]
    if account_id == "ACCT-001":
        # Northstar: P1=15min, P2=60min, P3=480min
        sla_targets["Enterprise"] = {"P1": 15, "P2": 60, "P3": 480}
    elif account_id == "ACCT-002":
        # LumenWorks: P1=120min, P2=240min, P3=960min (same as Growth default)
        pass  # Same as default Growth

    target_minutes = sla_targets.get(plan, sla_targets["Standard"]).get(severity, 480)
    deadline = created_at + pd.Timedelta(minutes=target_minutes)
    elapsed_minutes = (SNAPSHOT_DT - created_at).total_seconds() / 60

    breached = elapsed_minutes > target_minutes

    return {
        "ticket_id": ticket_id,
        "account_id": account_id,
        "plan": plan,
        "severity": severity,
        "target_minutes": target_minutes,
        "elapsed_minutes": round(elapsed_minutes, 1),
        "deadline": deadline.isoformat(),
        "breached": breached,
        "status": "BREACHED" if breached else "WITHIN_SLA",
        "source": f"{'Customer agreement' if account_id in ('ACCT-001', 'ACCT-002') else 'Support Policy v3'} — {plan} plan, {severity}",
    }
