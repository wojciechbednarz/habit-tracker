"""
Conversational AI coach (Bedrock Haiku-backed, stateful chat via conversation_id).
For habit-AI advice see ai.py."""

import asyncio
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends

from config import settings
from src.api.v1.routers.dependencies import get_ai_coach_service, get_current_active_user, get_habit_manager
from src.core.habit_async import AsyncHabitManager
from src.core.schemas import CoachContext, CoachRequest, CoachResponse, User
from src.infrastructure.ai.ai_coach import AICoachService

router = APIRouter(prefix=f"{settings.API_V1_STR}/coach", tags=["coach", "chat"])


@router.post("/chat")
async def chat(
    request: CoachRequest,
    ai_coach: Annotated[AICoachService, Depends(get_ai_coach_service)],
    habit_manager: Annotated[AsyncHabitManager, Depends(get_habit_manager)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> CoachResponse:
    """Endpoint for conversational AI coaching interactions."""

    at_risk = await habit_manager.get_at_risk_habits(current_user.user_id)
    at_risk = at_risk[:5]
    analytics = await asyncio.gather(*(habit_manager.get_habit_analytics(h.id) for h in at_risk))

    analytics_by_id = {h.id: a for h, a in zip(at_risk, analytics, strict=True)}
    context = CoachContext.from_at_risk(at_risk, analytics_by_id)
    async with ai_coach as coach:
        result = await coach.converse(request.message, context)
    return CoachResponse(
        reply=result.reply,
        conversation_id=request.conversation_id or uuid4(),
        tokens_used=result.tokens_used,
        latency_ms=result.latency_ms,
    )
