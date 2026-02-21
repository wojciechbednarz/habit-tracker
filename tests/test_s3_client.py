"""Tests functionalities of the S3Client"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.core.models import HabitBase, HabitCompletion
from src.infrastructure.aws.aws_helper import AWSSessionManager
from src.infrastructure.aws.s3_client import S3Client
from src.infrastructure.pdf.report_pdf import PDFGenerator
from src.infrastructure.pdf.reports_service import ReportService


@pytest.mark.asyncio
async def test_generate_report_and_send_to_s3_bucket(
    async_test_habits: list[HabitBase], mocked_habit_repository: AsyncMock
) -> None:
    """
    Generates HTML report, which is converted to PDF and then sent to AWS S3 bucket.
    TO BE REFACTORED - E.G. TO MOTO LIBRARY - CURRENTLY USING REAL AWS S3 SERVICE.
    """
    user_id = async_test_habits[0].user_id
    mock_active_habits = async_test_habits
    mock_repo = mocked_habit_repository
    mock_repo.get_all_habits_for_user.return_value = async_test_habits
    now = datetime.now(UTC)
    mock_completions = [HabitCompletion(id=uuid4(), habit_id=habit.id, completed_at=now) for habit in async_test_habits]
    mock_repo.get_completions_for_period.return_value = mock_completions
    report_gen = ReportService(mock_repo)
    report = await report_gen.calculate_weekly_stats(user_id=user_id)
    assert report is not None
    assert len(report.habits) == len(mock_active_habits)

    rendered_html = report_gen.render_html_report(report)
    pdf_gen = PDFGenerator()
    pdf_buffer = pdf_gen.create_pdf_buffer(rendered_html)
    session_manager = AWSSessionManager()
    s3_client = S3Client(session_manager)
    bucket_name = f"habit-tracker-test-{uuid4().hex[:8]}"
    key = "my-test-key"
    bucket = await s3_client.create_bucket(bucket_name)
    assert bucket is True
    upload_file_to_s3 = await s3_client.upload_file_to_bucket(bucket_name, pdf_buffer, key)
    assert upload_file_to_s3 is True
    await s3_client.get_object_from_bucket(bucket_name, key)
    await s3_client.delete_object_in_bucket(bucket_name, key)
    await s3_client.delete_bucket(bucket_name)
