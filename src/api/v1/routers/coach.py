"""
Conversational AI coach (Bedrock Haiku-backed, stateful chat via conversation_id).
For habit-AI advice see ai.py."""

from uuid import uuid4

from fastapi import APIRouter

from config import settings
from src.core.schemas import CoachReply, CoachRequest, CoachResponse

router = APIRouter(prefix=f"{settings.API_V1_STR}/coach", tags=["coach", "chat"])


@router.post("/chat")
async def chat(request: CoachRequest) -> CoachResponse:
    """Endpoint for conversational AI coaching interactions."""
    return CoachResponse(
        reply=CoachReply(reasoning="LLM reasoning", intent="advice", reply="LLM reply", next_action="none"),
        conversation_id=uuid4(),
        tokens_used=123,
        latency_ms=100,
    )
