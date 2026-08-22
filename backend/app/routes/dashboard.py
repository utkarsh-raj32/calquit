"""Proactive Issue Detection endpoints."""

from fastapi import APIRouter, Depends
from typing import List

from app.auth.models import UserContext
from app.auth.middleware import require_internal
from app.proactive.detector import run_proactive_analysis

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/insights")
async def get_dashboard_insights(user: UserContext = Depends(require_internal())):
    """Run proactive analysis and return insights for the dashboard.
    
    Only available to internal staff (support_agent, ops_manager).
    """
    insights = run_proactive_analysis(user)
    return insights
