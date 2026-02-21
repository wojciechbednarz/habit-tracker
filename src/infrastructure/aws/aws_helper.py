"""
AWS helper functions for creating clients and
fetching Cloud Formation stack information.
"""

from typing import Any

from aioboto3 import Session

from config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class AWSSessionManager:
    """Manages AWS sessions and clients with caching and region management."""

    def __init__(self, environment: str = "dev", region: str = settings.AWS_REGION) -> None:
        """
        Initializes the AWS session manager with environment and region.

        :param environment: Environment name ("dev" or "prod")
        :param region: AWS region name (e.g., "us-east-1")
        """
        self.region = region
        self.session = self.get_aws_session(environment)

    def change_region(self, new_region: str) -> None:
        """
        Changes region used in the AWS session. Removes cached client,
        so it will be recreated on next access.

        :new_region: New region to be set e.g "us-east-1"
        :return: None
        """
        self.region = new_region
        if hasattr(self, "client"):
            del self.client

    def get_aws_session(self, environment: str = "dev") -> Session:
        """
        Creates and caches an aioboto3 Session.
        Session is reusable and thread-safe.

        :param environment: Environment name ("dev" or "prod")
        :return: aioboto3 Session
        """
        logger.info(f"Creating aioboto3 session for environment: {environment}")
        configs = {
            "dev": {
                "region_name": settings.AWS_REGION,
                "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
            },
            "prod": {
                "region_name": settings.AWS_REGION,
                "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
            },
        }
        config = configs.get(environment, configs["dev"])
        return Session(**config)


async def get_cloud_formation_stack(stack_name: str, session_manager: AWSSessionManager) -> Any:
    """
    Fetches the Cloud Formation stack from the AWS.

    :stack_name: Name of the Cloud Formation stack
    :return: Stack details as a dictionary
    """
    logger.info(f"Fetching Cloud Formation stack: {stack_name}")
    session = session_manager.session
    async with session.client("cloudformation") as cf:
        response = await cf.describe_stacks(StackName=stack_name)
        stacks = response.get("Stacks", [])
        if not stacks:
            logger.error(f"No stack found with name: {stack_name}")
            return {}
        stack = stacks[0]
        logger.debug(f"Retrieved stack details: {stack}")
        return stack


async def get_sqs_queue_url(
    session_manager: AWSSessionManager,
    sqs_stack_name: str = settings.AWS_SQS_STACK_NAME,
) -> Any:
    """
    Fetches the SQS queue URL from the Cloud Formation stack outputs.

    :sqs_stack_name: Name of the Cloud Formation stack for SQS
    :return: SQS queue URL
    """
    logger.info(f"Fetching SQS queue URL from stack: {sqs_stack_name}")
    cf_stack = await get_cloud_formation_stack(sqs_stack_name, session_manager)
    outputs = cf_stack.get("Outputs", [])
    for output in outputs:
        if output["OutputKey"] == "ReportQueueUrl":
            logger.debug(f"Found SQS queue URL: {output['OutputValue']}")
            return output["OutputValue"]
    return ""


if __name__ == "__main__":
    import asyncio

    result = asyncio.run(get_sqs_queue_url(session_manager=AWSSessionManager("dev", settings.AWS_REGION)))
    print(f"SQS Queue URL: {result}")
