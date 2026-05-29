"""
Conversational AI coach (Bedrock Haiku-backed, stateful chat via conversation_id).
For habit-AI advice see ai.py."""

from typing import Annotated

from fastapi import APIRouter, Depends

from config import settings
from src.api.v1.routers.dependencies import get_ai_coach_service, get_habit_manager
from src.core.habit_async import AsyncHabitManager
from src.core.schemas import CoachRequest, CoachResponse
from src.infrastructure.ai.ai_coach import AICoachService

router = APIRouter(prefix=f"{settings.API_V1_STR}/coach", tags=["coach", "chat"])


@router.post("/chat")
async def chat(
    request: CoachRequest,
    ai_coach: Annotated[AICoachService, Depends(get_ai_coach_service)],
    habit_manager: Annotated[AsyncHabitManager, Depends(get_habit_manager)],
) -> CoachResponse:
    """Endpoint for conversational AI coaching interactions."""
    # return CoachResponse(
    #     reply=CoachReply(reasoning="LLM reasoning", intent="advice", reply="LLM reply", next_action="none"),
    #     conversation_id=uuid4(),
    #     tokens_used=123,
    #     latency_ms=100,
    # )
    # HOw to pass streak habits and at risk to the LLM?
    async with ai_coach as coach:
        await coach.converse(request.message, "some context")
    return CoachResponse(
        reply=coach.converse(request.message, "some context"),
        conversation_id="some_conversation_id",
        tokens_used=123,
        latency_ms=100,
    )
