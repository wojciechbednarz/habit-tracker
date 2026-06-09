"""This module defines the API endpoints for generating habit reports in the Habit Tracker application."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from config import settings
from src.api.v1.routers.dependencies import (
    get_current_active_user,
    get_s3_client,
    get_sqs_client,
)
from src.core.schemas import User
from src.infrastructure.aws.queue_client import SQSClient
from src.infrastructure.aws.s3_client import S3Client

router = APIRouter(prefix=f"{settings.API_V1_STR}/reports", tags=["reports"])


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def send_habit_report(
    current_user: Annotated[User, Depends(get_current_active_user)],
    queue_client: Annotated[SQSClient, Depends(get_sqs_client)],
) -> dict[str, str]:
    """Triggers habit report generation via POST request"""
    if current_user:
        await queue_client.send_report_trigger(current_user.user_id)
    return {"message": "Report generation started"}


@router.get("/{week}/download")
async def get_habit_report_presigned_url(
    current_user: Annotated[User, Depends(get_current_active_user)],
    s3_client: Annotated[S3Client, Depends(get_s3_client)],
    week: int,
) -> dict[str, str]:
    """Generates a presigned URL for downloading the habit report PDF for the given week."""
    key = f"reports/{current_user.user_id}/weekly_w{week}.pdf"
    check_url = await s3_client.head_object(settings.AWS_S3_BUCKET_NAME, key)
    if not check_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found. It may still be processing. Please try again later.",
        )
    presigned_url = await s3_client.generate_presigned_url(
        "get_object", {"Bucket": settings.AWS_S3_BUCKET_NAME, "Key": key}, 300
    )
    return {"url": presigned_url}
