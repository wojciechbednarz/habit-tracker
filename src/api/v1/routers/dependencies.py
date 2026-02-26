"""Dependency injection for API routers."""

from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from config import settings
from src.core.db import get_async_engine, get_session_maker
from src.core.events.handlers import Context
from src.core.habit_async import AsyncHabitManager, AsyncUserManager
from src.core.models import UserBase
from src.core.schemas import TokenData, User, UserInDB, UserWithRole
from src.core.security import decode_token, verify_password
from src.infrastructure.ai.ollama_client import OllamaClient
from src.infrastructure.aws.aws_helper import AWSSessionManager
from src.infrastructure.aws.dynamodb_client import DynamoDBClient
from src.infrastructure.aws.email_client import SESClient
from src.infrastructure.aws.queue_client import SQSClient
from src.repository.habit_repository import HabitRepository
from src.repository.user_repository import UserRepository
from src.utils.logger import setup_logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

logger = setup_logger(__name__)


async def get_user_manager() -> AsyncUserManager:
    """Returns user manager class for dependency injection"""
    return AsyncUserManager()


async def get_habit_manager() -> AsyncHabitManager:
    """Returns habit manager class  for dependency injection"""
    return AsyncHabitManager(ollama_client=OllamaClient())


async def get_redis_manager(request: Request) -> Any:
    """Returns redis manager class for dependency injection"""
    return request.app.state.redis_manager


async def authenticate_user(
    username: str,
    password: str,
    user_manager: Annotated[AsyncUserManager, Depends(get_user_manager)],
) -> UserBase | None:
    """Authenticates a user given a username and password"""
    user = await user_manager.get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, str(user.hashed_password)):
        print("WRONG PASSWORD")
        return None
    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_manager: Annotated[AsyncUserManager, Depends(get_user_manager)],
) -> UserInDB:
    """Returns the current user"""
    credentials_exceptions = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload is None:
            raise credentials_exceptions
        username = payload.get("sub")
        if username is None:
            raise credentials_exceptions
        token_data = TokenData(username=username)
    except InvalidTokenError as exc:
        raise credentials_exceptions from exc
    user_obj = await user_manager.get_user_by_username(username=token_data.username)
    user = UserInDB(**user_obj.to_dict())
    if user is None:
        raise credentials_exceptions
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Returns the currently active user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_user_with_role(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserWithRole:
    """Returns the currently active user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return UserWithRole(**current_user.model_dump())


async def require_admin(
    current_user: Annotated[UserWithRole, Depends(get_current_user_with_role)],
) -> UserWithRole:
    """Dependency to ensure user is an admin."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user


async def get_aws_session_manager() -> AWSSessionManager:
    """Returns an instance of AWSSessionManager for dependency injection."""
    return AWSSessionManager(environment="dev", region=settings.AWS_REGION)


async def get_ses_client(
    aws_session_manager: Annotated[AWSSessionManager, Depends(get_aws_session_manager)],
) -> SESClient:
    """
    Returns an instance of SESClient for dependency injection.

    :aws_session_manager: AWSSessionManager instance to initialize SESClient
    :return: SESClient instance
    """
    return SESClient(aws_session_manager)


async def get_sqs_client(
    aws_session_manager: Annotated[AWSSessionManager, Depends(get_aws_session_manager)],
) -> SQSClient:
    """
    Returns an instance of SQSClient for dependency injection.

    :aws_session_manager: AWSSessionManager instance to initialize SQSClient
    :return: SQSClient instance
    """
    return SQSClient(aws_session_manager)


async def get_user_repository() -> UserRepository:
    """Returns an instance of UserRepository for dependency injection."""
    return UserRepository(get_session_maker(get_async_engine()))


async def get_habit_repository() -> HabitRepository:
    """Returns an instance of HabitRepository for dependency injection."""
    return HabitRepository(get_session_maker(get_async_engine()), get_async_engine())


async def get_dynamodb_client() -> DynamoDBClient:
    """Returns an instance of DynamoDBClient for dependency injection."""
    aws_session_manager = await get_aws_session_manager()
    return DynamoDBClient(aws_session_manager)


async def get_events_context(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    habit_repo: Annotated[HabitRepository, Depends(get_habit_repository)],
    ses_client: Annotated[SESClient, Depends(get_ses_client)],
    dynamodb_client: Annotated[DynamoDBClient, Depends(get_dynamodb_client)],
) -> Context:
    """
    Returns a Context instance for dependency injection in event handlers.
    :user_repo: UserRepository instance to be injected into the Context
    :habit_repo: HabitRepository instance to be injected into the Context
    :ses_client: SESClient instance to be injected into the Context
    :return: Context instance with the injected dependencies
    """
    return Context(user_repo=user_repo, habit_repo=habit_repo, ses_client=ses_client, dynamo_db=dynamodb_client)


async def get_ollama_client() -> OllamaClient:
    """Returns an instance of OllamaClient for dependency injection."""
    return OllamaClient()
