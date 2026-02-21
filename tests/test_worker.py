import json
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from src.infrastructure.aws.email_client import SESClient
from src.infrastructure.aws.queue_client import SQSClient
from src.infrastructure.aws.s3_client import S3Client
from src.infrastructure.aws.worker import AppContainer, parse_message, process_message
from src.infrastructure.pdf.report_pdf import PDFGenerator
from src.infrastructure.pdf.reports_service import ReportService, WeeklyReport
from src.repository.user_repository import UserRepository

# ruff: noqa: E501

SQS_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"
SQS_VALID_MESSAGE = {
    "MessageId": "3d119015-8ee9-4dbc-9062-d4cc9e42b2c6",
    "ReceiptHandle": "AQEBS/o9PJ49l8aQwwhyoaMMAk4hQysQFKxVgMyWo18Ms1VmKHIvF6nqZ/qA3wYFOgKrfqlugO2DhLwwKfWEikLo+Ne9lhpWvtNOe4mfn5s6wDSBrchUml+UhxZKORIrzUs52K6ykAz6NoI+uU5nvFHPAAbSe2Dz4FrPe1XR8pgWGem9+rRKfCGI6FGm2HoGRiUg5SVGjNctDwa+xaBgyLxXiYXVSj6EIoc5rvC20Qhc4g33fPAf4yZcPcX80Fim3bFwWTfaWAEbt+gsUOyzp58cltufufue2VrajeVECEjbsJW/MGS4fQeq/I9RCJPVtKmcJfzMZw/TjzvlJnuZDKNaE7JsUohEFZs1mwobhVjXYyQbnJUVM332Tj32G3yHo941swKCcW4d3iG3qS+Iv2CGOg==",
    "MD5OfBody": "4dabe16ef43b79ed2306ee4943a2caef",
    "Body": '{"user_id":"17163844-da0f-4a0c-b802-8783ceb0fd7d"}',
}


def test_parse_message_valid_message() -> None:
    """Tests the parse_message function with a valid SQS message containing user_id and receipt_handle."""
    parsed_message = parse_message(SQS_VALID_MESSAGE)
    msg_body = json.loads(SQS_VALID_MESSAGE["Body"])
    msg_user_id = msg_body["user_id"]
    msg_receipt_handle = SQS_VALID_MESSAGE["ReceiptHandle"]
    assert parsed_message == (msg_user_id, msg_receipt_handle)


def test_parse_message_missing_body() -> None:
    """Tests the parse_message function with a message missing the 'Body' field, expecting a ValueError."""
    message = {
        "MessageId": "3d119015-8ee9-4dbc-9062-d4cc9e42b2c6",
        "ReceiptHandle": "AQEBS/o9PJ49l8aQwwhyoaMMAk4hQysQFKxVgMyWo18Ms1VmKHIvF6nqZ/qA3wYFOgKrfqlugO2DhLwwKfWEikLo+Ne9lhpWvtNOe4mfn5s6wDSBrchUml+UhxZKORIrzUs52K6ykAz6NoI+uU5nvFHPAAbSe2Dz4FrPe1XR8pgWGem9+rRKfCGI6FGm2HoGRiUg5SVGjNctDwa+xaBgyLxXiYXVSj6EIoc5rvC20Qhc4g33fPAf4yZcPcX80Fim3bFwWTfaWAEbt+gsUOyzp58cltufufue2VrajeVECEjbsJW/MGS4fQeq/I9RCJPVtKmcJfzMZw/TjzvlJnuZDKNaE7JsUohEFZs1mwobhVjXYyQbnJUVM332Tj32G3yHo941swKCcW4d3iG3qS+Iv2CGOg==",
        "MD5OfBody": "4dabe16ef43b79ed2306ee4943a2caef",
    }
    with pytest.raises(ValueError, match="Message missing 'Body' field"):
        parse_message(message)


def test_parse_message_missing_receipt_handle() -> None:
    """Tests the parse_message function with a message missing the 'ReceiptHandle' field, expecting a ValueError."""
    message = {
        "MessageId": "3d119015-8ee9-4dbc-9062-d4cc9e42b2c6",
        "MD5OfBody": "4dabe16ef43b79ed2306ee4943a2caef",
        "Body": '{"user_id":"17163844-da0f-4a0c-b802-8783ceb0fd7d"}',
    }
    with pytest.raises(ValueError, match="Message missing 'ReceiptHandle' field"):
        parse_message(message)


def test_parse_message_invalid_json_in_body() -> None:
    """Tests the parse_message function with a message containing invalid JSON in the 'Body' field, expecting a ValueError."""
    message = {
        "MessageId": "3d119015-8ee9-4dbc-9062-d4cc9e42b2c6",
        "ReceiptHandle": "AQEBS/o9PJ49l8aQwwhyoaMMAk4hQysQFKxVgMyWo18Ms1VmKHIvF6nqZ/qA3wYFOgKrfqlugO2DhLwwKfWEikLo+Ne9lhpWvtNOe4mfn5s6wDSBrchUml+UhxZKORIrzUs52K6ykAz6NoI+uU5nvFHPAAbSe2Dz4FrPe1XR8pgWGem9+rRKfCGI6FGm2HoGRiUg5SVGjNctDwa+xaBgyLxXiYXVSj6EIoc5rvC20Qhc4g33fPAf4yZcPcX80Fim3bFwWTfaWAEbt+gsUOyzp58cltufufue2VrajeVECEjbsJW/MGS4fQeq/I9RCJPVtKmcJfzMZw/TjzvlJnuZDKNaE7JsUohEFZs1mwobhVjXYyQbnJUVM332Tj32G3yHo941swKCcW4d3iG3qS+Iv2CGOg==",
        "MD5OfBody": "4dabe16ef43b79ed2306ee4943a2caef",
        "Body": '{"user_id" "17163844-da0f-4a0c-b802-8783ceb0fd7d"}',
    }
    with pytest.raises(ValueError, match="Message body is not valid JSON"):
        parse_message(message)


def test_parse_message_missing_user_id_in_body() -> None:
    """Tests the parse_message function with a message whose 'Body' field contains JSON missing the 'user_id' key, expecting a ValueError."""
    message = {
        "MessageId": "3d119015-8ee9-4dbc-9062-d4cc9e42b2c6",
        "ReceiptHandle": "AQEBS/o9PJ49l8aQwwhyoaMMAk4hQysQFKxVgMyWo18Ms1VmKHIvF6nqZ/qA3wYFOgKrfqlugO2DhLwwKfWEikLo+Ne9lhpWvtNOe4mfn5s6wDSBrchUml+UhxZKORIrzUs52K6ykAz6NoI+uU5nvFHPAAbSe2Dz4FrPe1XR8pgWGem9+rRKfCGI6FGm2HoGRiUg5SVGjNctDwa+xaBgyLxXiYXVSj6EIoc5rvC20Qhc4g33fPAf4yZcPcX80Fim3bFwWTfaWAEbt+gsUOyzp58cltufufue2VrajeVECEjbsJW/MGS4fQeq/I9RCJPVtKmcJfzMZw/TjzvlJnuZDKNaE7JsUohEFZs1mwobhVjXYyQbnJUVM332Tj32G3yHo941swKCcW4d3iG3qS+Iv2CGOg==",
        "MD5OfBody": "4dabe16ef43b79ed2306ee4943a2caef",
        "Body": '{"user_id": ""}',
    }
    with pytest.raises(ValueError, match="user_id missing in message body"):
        parse_message(message)


def test_parse_message_invalid_user_id_uuid() -> None:
    """Tests the parse_message function with a message whose 'Body' field contains a 'user_id' that is not a valid UUID, expecting a ValueError."""
    message = {
        "MessageId": "3d119015-8ee9-4dbc-9062-d4cc9e42b2c6",
        "ReceiptHandle": "AQEBS/o9PJ49l8aQwwhyoaMMAk4hQysQFKxVgMyWo18Ms1VmKHIvF6nqZ/qA3wYFOgKrfqlugO2DhLwwKfWEikLo+Ne9lhpWvtNOe4mfn5s6wDSBrchUml+UhxZKORIrzUs52K6ykAz6NoI+uU5nvFHPAAbSe2Dz4FrPe1XR8pgWGem9+rRKfCGI6FGm2HoGRiUg5SVGjNctDwa+xaBgyLxXiYXVSj6EIoc5rvC20Qhc4g33fPAf4yZcPcX80Fim3bFwWTfaWAEbt+gsUOyzp58cltufufue2VrajeVECEjbsJW/MGS4fQeq/I9RCJPVtKmcJfzMZw/TjzvlJnuZDKNaE7JsUohEFZs1mwobhVjXYyQbnJUVM332Tj32G3yHo941swKCcW4d3iG3qS+Iv2CGOg==",
        "MD5OfBody": "4dabe16ef43b79ed2306ee4943a2caef",
        "Body": '{"user_id": "123"}',
    }
    with pytest.raises(ValueError, match="user_id must be a valid UUID string"):
        parse_message(message)


@pytest.fixture
def app_container():
    container = AppContainer(
        sqs_client=AsyncMock(spec=SQSClient),
        s3_client=AsyncMock(spec=S3Client),
        ses_client=AsyncMock(spec=SESClient),
        pdf_generator=MagicMock(spec=PDFGenerator),
        report_service=MagicMock(spec=ReportService),
        user_repo=AsyncMock(spec=UserRepository),
        sqs_queue_url=SQS_QUEUE_URL,
    )
    return container


@pytest.mark.asyncio
async def test_process_message(app_container: AppContainer) -> None:
    """
    Tests the process_message function to ensure it calls the
    expected methods on the dependencies.

    :mock_app_container: A mocked AppContainer with AsyncMock dependencies
    :return: None
    """
    fake_report = WeeklyReport(
        user_id=UUID("17163844-da0f-4a0c-b802-8783ceb0fd7d"),
        start_date="2024-01-01",
        end_date="2024-01-07",
        week_number=1,
        habits=[
            {
                "name": "Drink Water",
                "total": 5,
                "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "status": "Completed",
            },
            {
                "name": "Exercise",
                "total": 3,
                "days": ["Monday", "Wednesday", "Friday"],
                "status": "In Progress",
            },
        ],
    )

    fake_html = """<html>
    <head><title>Weekly Report</title></head>
    <body>
    <h1>Weekly Report for User 17163844-da0f-4a0c-b802-8783ceb0fd7d</h1>
    <p>Report Period: 2024-01-01 to 2024-01-07</p>
    <p>Week Number: 1</p>
    <h2>Habits</h2>
    <ul>
    <li><strong>Drink Water</strong>: Completed 5 times on Monday, Tuesday, Wednesday, Thursday, Friday (Status: Completed)</li>
    <li><strong>Exercise</strong>: Completed 3 times on Monday, Wednesday, Friday (Status: In Progress)</li>
    </ul>
    </body>
    </html>"""

    fake_pdf = b"%PDF-1.4 fake pdf content"

    user_id = json.loads(SQS_VALID_MESSAGE["Body"])["user_id"]
    app_container.report_service.calculate_weekly_stats = AsyncMock()
    app_container.report_service.calculate_weekly_stats.return_value = fake_report
    app_container.report_service.render_html_report.return_value = fake_html
    app_container.pdf_generator.create_pdf_buffer.return_value = fake_pdf

    await process_message(app_container, SQS_VALID_MESSAGE)
    app_container.report_service.calculate_weekly_stats.assert_awaited_once_with(user_id)
    app_container.report_service.render_html_report.assert_called_once_with(fake_report)
    app_container.pdf_generator.create_pdf_buffer.assert_called_once_with(fake_html)
    app_container.s3_client.upload_file_to_bucket.assert_awaited_once()
    app_container.ses_client.send_email_with_attachment.assert_awaited_once()
    app_container.sqs_client.delete_message.assert_awaited_once()
