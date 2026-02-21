"""Report-related API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.api.v1.routers.dependencies import (
    get_current_active_user,
    get_sqs_client,
)
from src.core.schemas import User
from src.infrastructure.aws.queue_client import SQSClient

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def get_habit_report(
    current_user: Annotated[User, Depends(get_current_active_user)],
    queue_client: Annotated[SQSClient, Depends(get_sqs_client)],
) -> dict[str, str]:
    """Triggers habit report generation via POST request"""
    if current_user:
        await queue_client.send_report_trigger(current_user.user_id)
    return {"message": "Report generation started"}
