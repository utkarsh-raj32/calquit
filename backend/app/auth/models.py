"""Authentication models and utilities for ParcelPilot AI."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt

from app.config import JWT_SECRET, JWT_ALGORITHM


class UserRole(str, Enum):
    CUSTOMER = "customer"
    SUPPORT_AGENT = "support_agent"
    OPS_MANAGER = "ops_manager"


class UserContext(BaseModel):
    """Authenticated user context passed to every tool/agent call."""
    user_id: str
    role: UserRole
    account_id: Optional[str] = None  # Set for customer role
    name: str
    email: str


# Pre-defined mock users for the demo
MOCK_USERS = {
    # Customers (one per account)
    "northstar_user": UserContext(
        user_id="usr_northstar",
        role=UserRole.CUSTOMER,
        account_id="ACCT-001",
        name="Vikram Singh",
        email="vikram@northstarlogistics.com",
    ),
    "lumenworks_user": UserContext(
        user_id="usr_lumenworks",
        role=UserRole.CUSTOMER,
        account_id="ACCT-002",
        name="Sneha Patel",
        email="sneha@lumenworks.io",
    ),
    "beacon_user": UserContext(
        user_id="usr_beacon",
        role=UserRole.CUSTOMER,
        account_id="ACCT-003",
        name="Ravi Kumar",
        email="ravi@beaconretail.com",
    ),
    "axislabs_user": UserContext(
        user_id="usr_axislabs",
        role=UserRole.CUSTOMER,
        account_id="ACCT-004",
        name="Deepa Nair",
        email="deepa@axislabs.in",
    ),
    # Internal staff
    "rohit_agent": UserContext(
        user_id="usr_rohit",
        role=UserRole.SUPPORT_AGENT,
        name="Rohit Sharma",
        email="rohit@parcelpilot.com",
    ),
    "maya_agent": UserContext(
        user_id="usr_maya",
        role=UserRole.SUPPORT_AGENT,
        name="Maya Desai",
        email="maya@parcelpilot.com",
    ),
    "priya_manager": UserContext(
        user_id="usr_priya",
        role=UserRole.OPS_MANAGER,
        name="Priya Mehta",
        email="priya@parcelpilot.com",
    ),
}


def create_token(username: str) -> str:
    """Create a mock JWT token for a user."""
    if username not in MOCK_USERS:
        raise ValueError(f"Unknown user: {username}")
    user = MOCK_USERS[username]
    payload = {
        "sub": user.user_id,
        "username": username,
        "role": user.role.value,
        "account_id": user.account_id,
        "name": user.name,
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def get_user_from_token(token: str) -> UserContext:
    """Get UserContext from a JWT token."""
    payload = decode_token(token)
    username = payload.get("username")
    if username in MOCK_USERS:
        return MOCK_USERS[username]
    raise ValueError("Invalid token")
