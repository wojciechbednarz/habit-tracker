"""
AWS SDK CloudWatch client for handling CloudWatch operations.
"""

from botocore.exceptions import ClientError

from src.infrastructure.aws.aws_helper import AWSSessionManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

NAMESPACE_NAME = "HabitTracker"


class CloudWatchClient:
    """AWS SDK CloudWatch client for handling CloudWatch operations."""

    def __init__(self, session_manager: AWSSessionManager) -> None:
        self.session_manager = session_manager

    async def put_metric(self, name: str, value: float, unit: str = "Count") -> None:
        """
        Puts a custom metric to CloudWatch with the given name, value, and unit.
        :name: Name of the metric to be put to CloudWatch
        :value: Value of the metric to be put to CloudWatch
        :unit: Unit of the metric to be put to CloudWatch (default is "Count")
        :return: None
        """

        try:
            logger.debug("Putting metric to CloudWatch")
            async with self.session_manager.session.client("cloudwatch") as cw:
                await cw.put_metric_data(
                    Namespace=NAMESPACE_NAME,
                    MetricData=[
                        {
                            "MetricName": name,
                            "Value": value,
                            "Unit": unit,
                        }
                    ],
                )

        except ClientError as e:
            logger.error(f"Error encountered during putting metric to CloudWatch: {e}")

    async def retrieve_metric_alarms(self, alarm_names: list[str]) -> list[dict[str, str]]:
        """
        Retrieves the specified alarms from CloudWatch.
        :alarm_names: List of alarm names to retrieve from CloudWatch
        :return: List of dictionaries containing alarm details
        """
        try:
            logger.debug("Retrieving alarms from CloudWatch")
            async with self.session_manager.session.client("cloudwatch") as cw:
                response = await cw.describe_alarms(AlarmNames=alarm_names)
                alarms: list[dict[str, str]] = response.get("MetricAlarms", [])
                return alarms

        except ClientError as e:
            logger.error(f"Error encountered during retrieving alarms from CloudWatch: {e}")
            return []
