"""
AWS SDK SQS client for handling SQS queue operations.
"""

import json
import typing
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from botocore.exceptions import ClientError

from src.infrastructure.aws.aws_helper import AWSSessionManager, get_sqs_queue_url
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class SQSClient:
    """
    AWS SDK SQS client for handling SQS queue operations. (Producer)
    Used only for the SQS queue operations. The API imports this to push jobs to the
    SQS queue. Queue creation and configuration is handled via Cloud Formation stack.
    This client is used to send messages to the SQS queue, receive messages from the
    SQS queue, and delete messages from the SQS queue.
    """

    def __init__(self, session_manager: AWSSessionManager) -> None:
        self.session_manager = session_manager

    async def send_report_trigger(self, user_id: UUID) -> None:
        """
        Sends a message to the SQS queue to trigger \n        report generation for the given user ID.

        :user_id: ID of the user for whom the report generation is triggered
        :return: None
        """
        url = await get_sqs_queue_url(self.session_manager)
        await self.send_message(user_id, url)

    async def send_message(self, user_id: UUID, queue_url: str) -> dict[str, Any]:
        """
        Sends a message to the SQS queue with the given user ID.

        :user_id: ID of the user for whom the message is sent
        :queue_url: URL of the SQS queue
        :return: Response from SQS send_message API
        """
        try:
            logger.info(f"Sending message to SQS queue: {queue_url} for user with ID: {user_id}")
            async with self.session_manager.session.client("sqs") as sqs:
                message_body = json.dumps(
                    {
                        "user_id": str(user_id),
                        "request_time": datetime.now(UTC).isoformat(),
                    }
                )
                response = await sqs.send_message(QueueUrl=queue_url, MessageBody=message_body)
                return typing.cast(dict[str, Any], response)
        except ClientError as e:
            logger.error(f"Error encountered during sending message to SQS queue: {e}")
            raise RuntimeError("Failed to send message to SQS queue") from e

    async def receive_message(self, queue_url: str, max_messages: int, wait_time_seconds: int) -> dict[str, Any]:
        """
        Receives a message from the SQS queue.

        :queue_url: URL of the SQS queue
        :return: Response from SQS receive_message API
        """
        try:
            logger.info(f"Receiving message from SQS queue: {queue_url}")
            async with self.session_manager.session.client("sqs") as sqs:
                response = await sqs.receive_message(
                    QueueUrl=queue_url,
                    MaxNumberOfMessages=max_messages,
                    WaitTimeSeconds=wait_time_seconds,
                )
                return typing.cast(dict[str, Any], response)
        except ClientError as e:
            logger.error(f"Error encountered during receiving message from SQS queue: {e}")
            raise RuntimeError("Failed to receive message from SQS queue") from e

    async def delete_message(self, queue_url: str, receipt_handle: str) -> dict[str, Any]:
        """
        Deletes a message from the SQS queue.

        :queue_url: URL of the SQS queue
        :receipt_handle: Receipt handle of the message to be deleted.
        This is obtained when receiving the message.
        :return: Response from SQS delete_message API
        """
        try:
            logger.info(f"Receiving message from SQS queue: {queue_url}")
            async with self.session_manager.session.client("sqs") as sqs:
                response = await sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
                return typing.cast(dict[str, Any], response)
        except ClientError as e:
            logger.error(f"Error encountered during deleting message from SQS queue: {e}")
            raise RuntimeError("Failed to delete message from SQS queue") from e
