"""Tests functionalities of the S3Client"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
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
    Tests the end-to-end report generation and S3 upload flow using mocks.
    """
    user_id = async_test_habits[0].user_id
    mock_repo = mocked_habit_repository
    mock_repo.get_all_habits_for_user.return_value = async_test_habits
    now = datetime.now(UTC)
    mock_completions = [HabitCompletion(id=uuid4(), habit_id=habit.id, completed_at=now) for habit in async_test_habits]
    mock_repo.get_completions_for_period.return_value = mock_completions

    report_gen = ReportService(mock_repo)
    report = await report_gen.calculate_weekly_stats(user_id=user_id)
    assert report is not None

    rendered_html = report_gen.render_html_report(report)
    pdf_gen = PDFGenerator()
    pdf_buffer = pdf_gen.create_pdf_buffer(rendered_html)

    # Mock AWS Session and Client
    mock_session = MagicMock()  # Changed from AsyncMock
    mock_s3_client = AsyncMock()

    # Setup the async context manager for session.client("s3")
    # session.client("s3") is synchronous, returns an object used in "async with"
    context_manager = MagicMock()
    context_manager.__aenter__.return_value = mock_s3_client
    mock_session.client.return_value = context_manager

    session_manager = MagicMock(spec=AWSSessionManager)
    session_manager.session = mock_session
    session_manager.region = "eu-central-1"

    s3_client = S3Client(session_manager)
    bucket_name = "test-bucket"
    key = "my-test-key"

    # Mock internal methods to avoid real network calls
    with (
        patch.object(S3Client, "check_if_bucket_exists", return_value=False),
        patch.object(S3Client, "get_bucket_list", return_value={"Buckets": []}),
    ):
        # Test create_bucket
        mock_s3_client.create_bucket.return_value = {}
        bucket_created = await s3_client.create_bucket(bucket_name)
        assert bucket_created is True

        # Test upload
        mock_s3_client.upload_fileobj.return_value = None
        uploaded = await s3_client.upload_file_to_bucket(bucket_name, pdf_buffer, key)
        assert uploaded is True

        # Test get object
        mock_s3_client.get_object.return_value = {"Body": "fake-body"}
        obj = await s3_client.get_object_from_bucket(bucket_name, key)
        assert obj["Body"] == "fake-body"

        # Test delete
        mock_s3_client.delete_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 204}}
        del_obj = await s3_client.delete_object_in_bucket(bucket_name, key)
        assert del_obj["ResponseMetadata"]["HTTPStatusCode"] == 204

        mock_s3_client.delete_bucket.return_value = {}
        bucket_deleted = await s3_client.delete_bucket(bucket_name)
        assert bucket_deleted is True
