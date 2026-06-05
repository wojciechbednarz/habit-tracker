import pytest
from botocore.exceptions import ClientError

from config import settings
from src.api.main import app
from src.api.v1.routers.dependencies import get_ai_coach_service
from src.core.schemas import CoachContext, CoachReply, CoachResponse
from src.infrastructure.ai.ai_coach import AICoachService, CoachResult


class FakeAICoachService(AICoachService):
    def __init__(self, *, raises: Exception | None = None) -> None:
        self._raises = raises

    async def __aenter__(self) -> "FakeAICoachService":
        return self

    async def __aexit__(self, *a) -> None:
        pass

    async def converse(self, msg, ctx) -> CoachResult:
        self.received_msg = msg
        self.received_ctx = ctx
        if self._raises:
            raise self._raises
        else:
            return CoachResult(
                reply=CoachReply(
                    reasoning="Keep going!",
                    intent="encourage",
                    reply="Try morning workouts.",
                    next_action="suggest_habit",
                ),
                tokens_used=123,
                latency_ms=100,
            )


@pytest.mark.integration
def test_coach_chat_happy(authenticated_as_user_api_client):
    client = authenticated_as_user_api_client
    fake = FakeAICoachService()
    app.dependency_overrides[get_ai_coach_service] = lambda: fake
    resp = client.post(f"{settings.API_V1_STR}/coach/chat", json={"message": "I missed 3 workouts"})

    assert resp.status_code == 200
    assert CoachResponse.model_validate(resp.json())
    assert resp.json()["reply"]["intent"] == "encourage"
    assert resp.json()["tokens_used"] == 123
    assert fake.received_msg == "I missed 3 workouts"
    assert isinstance(fake.received_ctx, CoachContext)


@pytest.mark.integration
def test_coach_chat_throttled(authenticated_as_user_api_client):
    client = authenticated_as_user_api_client
    fake = FakeAICoachService(
        raises=ClientError({"Error": {"Code": "ThrottlingException", "Message": "slow"}}, "Converse")
    )
    app.dependency_overrides[get_ai_coach_service] = lambda: fake

    resp = client.post(f"{settings.API_V1_STR}/coach/chat", json={"message": "hi"})
    assert resp.status_code == 429
