"""Module for polling SQS queue, processing messages, and sending emails using SES."""

import asyncio
import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncEngine

from config import settings
from src.core.db import get_async_engine, get_session_maker
from src.infrastructure.aws.aws_helper import AWSSessionManager, get_sqs_queue_url
from src.infrastructure.aws.email_client import SESClient
from src.infrastructure.aws.queue_client import SQSClient
from src.infrastructure.aws.s3_client import S3Client
from src.infrastructure.pdf.report_pdf import PDFGenerator
from src.infrastructure.pdf.reports_service import ReportService
from src.repository.habit_repository import HabitRepository
from src.repository.user_repository import UserRepository
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class AppContainer:
    """Dependency injection container."""

    sqs_client: SQSClient
    s3_client: S3Client
    ses_client: SESClient
    pdf_generator: PDFGenerator
    report_service: ReportService
    user_repo: UserRepository
    sqs_queue_url: str

    @classmethod
    def create(cls, engine: AsyncEngine, sqs_queue_url: str, session_manager: AWSSessionManager) -> "AppContainer":
        """Factory method to wire up all dependencies"""
        sqs_client = SQSClient(session_manager)
        s3_client = S3Client(session_manager)
        ses_client = SESClient(session_manager)
        pdf_generator = PDFGenerator()
        habit_repo = HabitRepository(get_session_maker(engine), engine)
        user_repo = UserRepository(get_session_maker(engine))
        report_service = ReportService(habit_repo)
        return cls(
            sqs_client=sqs_client,
            sqs_queue_url=sqs_queue_url,
            s3_client=s3_client,
            ses_client=ses_client,
            pdf_generator=pdf_generator,
            report_service=report_service,
            user_repo=user_repo,
        )


def parse_message(message: dict[str, Any]) -> tuple[UUID, str]:
    """
    Parses SQS message to extract user_id and receipt_handle

    :message: SQS message dictionary
    :return: Tuple of (user_id, receipt_handle)
    """
    if "Body" not in message:
        raise ValueError("Message missing 'Body' field")
    if "ReceiptHandle" not in message:
        raise ValueError("Message missing 'ReceiptHandle' field")
    try:
        body = json.loads(message["Body"])
        if not body:
            raise ValueError("Message missing 'Body' field")
    except (TypeError, json.JSONDecodeError) as e:
        raise ValueError("Message body is not valid JSON") from e
    if "user_id" not in body or not body["user_id"]:
        raise ValueError("user_id missing in message body")
    if not isinstance(body["user_id"], str):
        raise ValueError("user_id must be a string")
    try:
        UUID(body["user_id"])
    except (ValueError, AttributeError, TypeError) as e:
        raise ValueError("user_id must be a valid UUID string") from e
    user_id = body["user_id"]
    receipt_handle = message["ReceiptHandle"]
    return UUID(user_id), str(receipt_handle)


async def process_message(
    container: AppContainer,
    message: dict[str, Any],
) -> None:
    """
    Process a single SQS message

    :container: AppContainer with dependencies
    :message: SQS message dictionary
    :return: None
    """

    logger.info(f"Processing message with ID: {message.get('MessageId', 'N/A')}")
    user_id, receipt_handle = parse_message(message)

    try:
        report = await container.report_service.calculate_weekly_stats(user_id)
        if report is None:
            logger.warning(f"No habits for user {user_id}, skipping.")
            return
        html_string = container.report_service.render_html_report(report)
        pdf_buffer = container.pdf_generator.create_pdf_buffer(html_string)

        s3_key = f"reports/{user_id}/weekly_w{report.week_number}.pdf"
        await container.s3_client.upload_file_to_bucket(
            bucket_name=settings.AWS_S3_BUCKET_NAME, buffer=pdf_buffer, key=s3_key
        )
        user_data = await container.user_repo.get_by_id(user_id)
        if not user_data:
            raise ValueError(f"User with ID {user_id} not found in database")
        await container.ses_client.send_email_with_attachment(
            attachment=pdf_buffer,
            recipient=str(user_data.email),
            sender=settings.AWS_SES_SENDER_EMAIL,
            subject=f"Your Weekly Report - {report.period_label}",
        )
        await container.sqs_client.delete_message(
            queue_url=container.sqs_queue_url,
            receipt_handle=receipt_handle,
        )
        logger.info(f"Successfully processed report for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to process message for user {user_id}: {e}", exc_info=True)
        raise


async def main() -> None:
    """Main worker function to poll SQS, process messages, and send emails."""
    engine = get_async_engine()
    session_manager = AWSSessionManager(environment="dev", region=settings.AWS_REGION)
    sqs_queue_url = await get_sqs_queue_url(session_manager)
    container = AppContainer.create(engine, sqs_queue_url, session_manager)
    logger.info("Starting SQS worker...")
    try:
        while True:
            try:
                receive_message = await container.sqs_client.receive_message(
                    queue_url=container.sqs_queue_url,
                    max_messages=10,
                    wait_time_seconds=20,
                )
                if not receive_message:
                    logger.debug("No messages received, continuing to poll...")
                    continue
                messages = receive_message.get("Messages", [])
                tasks = [process_message(container, msg) for msg in messages]
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)
    except KeyboardInterrupt:
        logger.info("Shutting down worker...")
    finally:
        await engine.dispose()
        logger.info("Worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
