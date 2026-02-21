"""AWS SDK SES client for handling email operations"""

import typing
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from io import BytesIO
from typing import Any

from botocore.exceptions import ClientError

from src.infrastructure.aws.aws_helper import AWSSessionManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class SESClient:
    """
    AWS SDK SES client for handling email operations. (Notifier)
    Usage: The worker service imports this to send emails.
    """

    def __init__(self, session_manager: AWSSessionManager) -> None:
        self.session_manager = session_manager

    def _add_attachment(self, msg_object: MIMEMultipart, attachment: BytesIO, filename: str) -> MIMEMultipart:
        """
        Adds attachment to the email message object

        :msg_object: MIMEMultipart email message object
        :return: None
        """
        attachment.seek(0)
        part = MIMEApplication(attachment.read(), _subtype="pdf")
        part.add_header("Content-Disposition", "attachment", filename=filename)
        msg_object.attach(part)
        return msg_object

    def _build_email_message_object(
        self,
        subject: str,
        sender: str,
        recipient: str,
        attachment: BytesIO,
        filename: str,
    ) -> MIMEMultipart:
        """
        Builds the email message with attachment

        :subject: Subject of the email
        :sender: Sender email address
        :recipient: Recipient email address
        :return: MIMEMultipart email message object
        """
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient
        self._add_attachment(msg, attachment, filename)
        return msg

    async def send_email_with_attachment(
        self,
        attachment: BytesIO,
        recipient: str,
        sender: str,
        subject: str = "Your Weekly Habit Tracker Report",
    ) -> dict[str, Any]:
        """
        Sends an email with attachment using AWS SES.

        :attachment: Attachment file as BytesIO
        :recipient: Recipient email address
        :sender: Sender email address
        :return: Response from SES send_raw_email API
        """
        logger.info("Sending email with attachment using SES")
        logger.info(f"ATTACHMENT: {attachment}, TYPE: {type(attachment)}")
        try:
            msg = self._build_email_message_object(
                subject=subject,
                sender=sender,
                recipient=recipient,
                attachment=attachment,
                filename="weekly_report.pdf",
            )
            async with self.session_manager.session.client("ses", region_name=self.session_manager.region) as client:
                config = {
                    "Source": sender,
                    "Destinations": [recipient],
                    "RawMessage": {"Data": msg.as_string().encode("utf-8")},
                }
                response = await client.send_raw_email(**config)
                logger.info(f"Congratulation email sent successfully. Message ID: {response['MessageId']}")
                return typing.cast(dict[str, Any], response)
        except ClientError as e:
            logger.error(f"Error encountered during sending email: {e}")
            raise RuntimeError("Sending email with attachment not successful") from e

    async def send_congratulation_email(
        self,
        achievement_type: str,
        recipient: str,
        sender: str,
        subject: str = "Congratulations on Your Achievement!",
    ) -> dict[str, Any]:
        """Sends a congratulation email without attachment using AWS SES."""
        logger.info("Sending congratulation email using SES")
        try:
            async with self.session_manager.session.client("ses", region_name=self.session_manager.region) as client:
                config = {
                    "Source": sender,
                    "Destination": {"ToAddresses": [recipient]},
                    "Message": {
                        "Subject": {"Data": subject},
                        "Body": {
                            "Text": {"Data": "Congratulations!  You've unlocked a new achievement: {achievement_type}"}
                        },
                    },
                }
                response = await client.send_email(**config)
                logger.info(f"Congratulation email sent successfully. Message ID: {response['MessageId']}")
                return typing.cast(dict[str, Any], response)
        except ClientError as e:
            logger.error(f"Error encountered during sending congratulation email: {e}")
            raise RuntimeError("Sending congratulation email not successful") from e
