"""FastAPI middleware for authentication and access control."""

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.auth.models import UserContext, UserRole, get_user_from_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> UserContext:
    """Extract and validate the current user from the Authorization header."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        user = get_user_from_token(credentials.credentials)
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_role(*roles: UserRole):
    """Dependency that checks if the current user has one of the required roles."""
    async def role_checker(user: UserContext = Depends(get_current_user)) -> UserContext:
        if user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user.role.value}' does not have access to this resource",
            )
        return user
    return role_checker


def require_internal():
    """Shorthand: require support_agent or ops_manager role."""
    return require_role(UserRole.SUPPORT_AGENT, UserRole.OPS_MANAGER)
