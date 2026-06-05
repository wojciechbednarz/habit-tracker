import time
from dataclasses import dataclass
from typing import Any

from aioboto3.session import Session
from types_aiobotocore_bedrock.client import BedrockClient

from config import settings
from src.core.schemas import CoachContext, CoachReply
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class CoachResult:
    reply: CoachReply
    tokens_used: int
    latency_ms: int


class AICoachService:
    """Bedrock LLM implementation for AI coaching"""

    def __init__(self, model: str = settings.AWS_BEDROCK_LLM_MODEL_ID) -> None:
        """Initialization of the AICoachService"""
        self.model: str = model
        self.session = Session(region_name=settings.AWS_REGION)
        self.client: BedrockClient | None = None

    async def __aenter__(self) -> "AICoachService":
        """Initializes the BedrockClient"""
        logger.debug("Initializing BedrockClient connection.")
        if self.session is None:
            self.session = Session()
        if self.client is None:
            self._cm = self.session.client("bedrock-runtime")
            self.client = await self._cm.__aenter__()
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: Any) -> None:
        """Closes the BedrockClient connection"""
        logger.debug("Closing BedrockClient connection.")
        if self.client:
            await self.client.__aexit__(exc_type, exc, tb)
            self.client = None

    async def converse(self, user_message: str, user_habit_context: CoachContext) -> CoachResult:
        """
        LLM query to trigger coaching advice based on habit context
        user_message: Message provided by the user
        user_habit_context: Habit streaks, missed habits - related to the user.
        This can be obtained via AsyncHabitManager methods.
        """
        if self.client is None:
            raise RuntimeError("client not initialized — use 'async with'")
        conversation = [
            {"role": "user", "content": [{"text": user_message}]},
        ]
        system = [
            {
                "text": f"You are a habit coach mentor. Your task is to provide user"
                f"feedback based on the user habit context: {user_habit_context}"
            }
        ]
        start = time.perf_counter()
        response = await self.client.converse(
            modelId=self.model,
            messages=conversation,
            system=system,
            inferenceConfig={
                "maxTokens": 512,
                "temperature": 0.5,
            },
            toolConfig={
                "tools": [
                    {
                        "toolSpec": {
                            "name": "coach_reply",
                            "description": "emit a structured coach reply",
                            "inputSchema": {"json": CoachReply.model_json_schema()},
                        }
                    }
                ],
                "toolChoice": {"tool": {"name": "coach_reply"}},
            },
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        tokens_used = response["usage"]["totalTokens"]
        content = response["output"]["message"]["content"]
        for elem in content:
            if "toolUse" in elem:
                coach_reply = CoachReply.model_validate(elem["toolUse"]["input"])
        if coach_reply is None:
            raise RuntimeError(f"expected tool call, got stopReason={response['stopReason']}")
        logger.info(f"LLM response text: {coach_reply}")
        return CoachResult(reply=coach_reply, tokens_used=tokens_used, latency_ms=latency_ms)
