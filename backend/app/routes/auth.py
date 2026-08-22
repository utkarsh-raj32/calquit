"""Authentication endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.auth.models import create_token, MOCK_USERS

router = APIRouter(prefix="/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    username: str


class LoginResponse(BaseModel):
    token: str
    user: dict


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Mock login endpoint for demo purposes.
    
    Accepts a username (e.g., 'northstar_user', 'maya_agent') and returns a JWT.
    """
    if request.username not in MOCK_USERS:
        raise HTTPException(status_code=401, detail="Invalid mock username")
    
    token = create_token(request.username)
    user = MOCK_USERS[request.username]
    
    return {
        "token": token,
        "user": {
            "user_id": user.user_id,
            "role": user.role.value,
            "account_id": user.account_id,
            "name": user.name,
            "email": user.email,
        }
    }


@router.get("/users")
async def list_mock_users():
    """Return the list of available mock users for the frontend selector."""
    users = []
    for username, u in MOCK_USERS.items():
        users.append({
            "username": username,
            "name": u.name,
            "role": u.role.value,
            "account_id": u.account_id,
        })
    return {"users": users}
