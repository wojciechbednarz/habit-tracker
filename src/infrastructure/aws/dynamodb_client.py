"""
AWS SDK DynamoDB client for handling storage operations, mostly related to
achievements.
"""

from typing import Any, cast
from uuid import UUID

from botocore.exceptions import ClientError

from config import settings
from src.infrastructure.aws.aws_helper import AWSSessionManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class DynamoDBClient:
    def __init__(self, session_manager: AWSSessionManager) -> None:
        """Initializes DynamoDBClient"""
        self.session_manager = session_manager

    async def put_streak(self, user_id: UUID, habit_id: UUID, streak_count: int) -> dict[str, Any]:
        """
        Creates or replaces the existing habit streak with the new one.

        :user_id: Unique ID of the user
        :habit_id: Unique ID of the habit
        :streak_count: Current streak count for the habit
        :return: Response from DynamoDB put_item operation
        """
        logger.info(f"Putting streak for user_id: {user_id}, habit_id: {habit_id}, streak_count: {streak_count}")
        try:
            async with self.session_manager.session.client("dynamodb") as dynamodb:
                item = {
                    "PK": {"S": f"USER#{str(user_id)}"},
                    "SK": {"S": f"STREAK#{str(habit_id)}"},
                    "StreakCount": {"N": str(streak_count)},
                }
                response = await dynamodb.put_item(
                    Item=item, ReturnConsumedCapacity="Total", TableName=settings.AWS_DYNAMODB_TABLE_NAME
                )
                logger.info(
                    f"Successfully put streak for user_id: {user_id}, habit_id:{habit_id}, streak_count: {streak_count}"
                )
                return cast(dict[str, Any], response)
        except ClientError as e:
            logger.error(f"Failed to put streak for user_id: {user_id}, habit_id: {habit_id}. Error: {e}")
            raise RuntimeError("Failed to put streak in DynamoDB") from e

    async def update_points(self, user_id: UUID, points: int) -> dict[str, Any]:
        """
        Updates the user's points by adding the given points to the existing points.
        METADATA - type of the item that stores user metadata, including total points.
        This is used to distinguish it from other items in the same partition
        (USER#<user_id>) that store different types.

        :user_id: Unique ID of the user
        :points: Points to be added to the user's existing points
        :return: Response from DynamoDB update_item operation
        """
        try:
            async with self.session_manager.session.client("dynamodb") as dynamodb:
                key = {"PK": {"S": f"USER#{str(user_id)}"}, "SK": {"S": "METADATA"}}
                update_expression = "ADD TotalPoints :inc SET EntityType = :etype"
                expression_attribute_values = {":inc": {"N": str(points)}, ":etype": {"S": "USER"}}
                response = await dynamodb.update_item(
                    Key=key,
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_attribute_values,
                    ReturnValues="UPDATED_NEW",
                    TableName=settings.AWS_DYNAMODB_TABLE_NAME,
                )
                logger.info(f"Successfully updated points for user_id: {user_id}, points: {points}")
                return cast(dict[str, Any], response)
        except ClientError as err:
            logger.error(f"Error during updating points for a user: {err}")
            raise RuntimeError("Failed to update points in DynamoDB") from err

    async def get_streak(self, user_id: UUID, habit_id: UUID) -> int:
        """
        Gets the current streak count for a specific habit of a user.

        :user_id: Unique ID of the user
        :habit_id: Unique ID of the habit
        :return: Current streak count for the habit
        """
        try:
            async with self.session_manager.session.client("dynamodb") as dynamodb:
                key = {"PK": {"S": f"USER#{str(user_id)}"}, "SK": {"S": f"STREAK#{str(habit_id)}"}}
                response = await dynamodb.get_item(
                    TableName=settings.AWS_DYNAMODB_TABLE_NAME,
                    Key=key,
                )
                streak_count_number = response.get("Item", {}).get("StreakCount", {}).get("N")
                if streak_count_number is None:
                    logger.info(f"No streak found for user_id: {user_id}, habit_id: {habit_id}. Returning 0.")
                    return 0
                logger.info(
                    f"Successfully got streak for user_id: {user_id}, habit_id:"
                    f"{habit_id}, streak_count: {streak_count_number}"
                )
                return int(streak_count_number)
        except ClientError as e:
            logger.error(f"Failed to get streak for user_id: {user_id}, habit_id:{habit_id}. Error: {e}")
            raise RuntimeError("Failed to get streak from DynamoDB") from e
