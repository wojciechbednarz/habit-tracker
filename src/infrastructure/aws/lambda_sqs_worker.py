import asyncio
import json
from typing import Any
from uuid import UUID

from config import settings
from src.core.db import get_async_engine
from src.infrastructure.aws.aws_helper import AWSSessionManager, get_sqs_queue_url
from src.infrastructure.aws.worker import AppContainer
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


async def _process_event(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Processes the SQS event to generate and send weekly reports for users.
    :event: Plain dict coming from SQS:
            {
        "Records": [
            {
            "messageId": "059f36b4-87a3-44ab-83d2-661975830a7d",
            "receiptHandle": "AQEB...",
            "body": "{\"user_id\": 42, \"report\": {\"week_number\": 26}}",
            "attributes": {
                "ApproximateReceiveCount": "1",
                "SentTimestamp": "1719750000000"
            },
            "messageAttributes": {},
            "md5OfBody": "...",
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:eu-central-1:...:habit-reports",
            "awsRegion": "eu-central-1"
            }
        ]
        }
    :context: AWS Lambda context object
    :return: Dictionary containing batch item failures, if any
    """

    engine = get_async_engine()
    session_manager = AWSSessionManager(environment="dev", region=settings.AWS_REGION)
    sqs_queue_url = await get_sqs_queue_url(session_manager)
    app_container = AppContainer.create(engine, sqs_queue_url, session_manager)

    failures = []
    records = event.get("Records", [])
    try:
        for record in records:
            message_id = record.get("messageId")

            try:
                body: str = record.get("body")

                user_id = UUID(json.loads(body)["user_id"])
                report = await app_container.report_service.calculate_weekly_stats(user_id)
                if report is None:
                    logger.warning(f"No habits for user {user_id}, skipping.")
                    continue

                s3_key = f"reports/{user_id}/weekly_w{report.week_number}.pdf"
                if await app_container.s3_client.object_exists(settings.AWS_S3_BUCKET_NAME, s3_key):
                    continue

                stats = report
                html = await asyncio.to_thread(app_container.report_service.render_html_report, stats)
                pdf = await asyncio.to_thread(app_container.pdf_generator.create_pdf_buffer, html)

                await app_container.s3_client.upload_file_to_bucket(
                    bucket_name=settings.AWS_S3_BUCKET_NAME, buffer=pdf, key=s3_key
                )
                user_data = await app_container.user_repo.get_by_id(user_id)
                if not user_data:
                    raise ValueError(f"User with ID {user_id} not found in database")
                await app_container.ses_client.send_email_with_attachment(
                    attachment=pdf,
                    recipient=str(user_data.email),
                    sender=settings.AWS_SES_SENDER_EMAIL,
                    subject=f"Your Weekly Report - {report.period_label}",
                )

            except Exception:
                logger.error({"itemIdentifier": message_id})
                failures.append({"itemIdentifier": message_id})
                await app_container.cloudwatch_client.put_metric("ReportGenerationFailures", 1)
        return {"batchItemFailures": failures}
    finally:
        await engine.dispose()


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    return asyncio.run(_process_event(event, context))
