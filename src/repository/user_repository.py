"""Repository pattern methods for a user"""

from abc import abstractmethod
from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.exceptions import (
    DatabaseException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from src.core.models import UserBase
from src.repository.base import BaseRepository
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

T = TypeVar("T")


class IUserRespository(BaseRepository[UserBase]):
    """Extension class for additional user methods"""

    @abstractmethod
    async def get_by_email(self, email: str) -> T | None:
        """Gets entity using email address"""
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> T | None:
        """Gets entity using username"""
        pass

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if entity exists by email."""
        pass

    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """Check if entity exists by username."""
        pass


class UserRepository(BaseRepository[UserBase]):
    """Handles database operations for User entities using SQLAlchemy ORM."""

    def __init__(self, async_session_maker: async_sessionmaker[AsyncSession]) -> None:
        """Initializes the UserRepository with an async session maker."""
        self.async_session_maker = async_session_maker

    async def add(self, entity: UserBase) -> UserBase:
        """Persists a user entity to the database."""
        try:
            async with self.async_session_maker() as session:
                session.add(entity)
                await session.commit()
                await session.refresh(entity)
                return entity
        except IntegrityError as e:
            logger.error(f"User {entity.username} already exists: {e}")
            raise UserAlreadyExistsException(
                f"User with username '{entity.username}' or email '{entity.email}' "
                f"already exists"
            ) from e
        except SQLAlchemyError as e:
            logger.error(f"Database error while adding user {entity.username}: {e}")
            raise DatabaseException(
                f"Failed to add user {entity.username}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error while adding user {entity.username}: {e}")
            raise DatabaseException(
                f"Unexpected error while adding user: {str(e)}"
            ) from e

    async def delete(self, entity_id: UUID) -> bool:
        """Performs delete of the user entity from the database."""
        async with self.async_session_maker() as session:
            try:
                query = delete(UserBase).where(UserBase.user_id == entity_id)
                result = await session.execute(query)
                await session.commit()
                deleted: bool = bool(result.rowcount) if result.rowcount else False  # type: ignore[attr-defined]
                return deleted
            except SQLAlchemyError as e:
                logger.error(f"Database error while deleting user {entity_id}: {e}")
                raise DatabaseException(f"Failed to delete user: {str(e)}") from e
            except UserNotFoundException:
                raise
            except Exception as e:
                logger.error(
                    f"Unexpected error while deleting user by ID {entity_id}: {e}"
                )
                raise DatabaseException(
                    f"Unexpected error while deleting user by ID {entity_id}: {str(e)}"
                ) from e

    async def update(self, entity_id: UUID, params: dict[str, Any]) -> bool:
        """Performs update of the user entity in the database."""
        logger.info(f"Updating user with user ID: {entity_id}")
        async with self.async_session_maker() as session:
            try:
                query = (
                    update(UserBase)
                    .where(UserBase.user_id == entity_id)
                    .values(**params)
                )
                result = await session.execute(query)
                await session.commit()
                updated: bool = bool(result.rowcount) > 0  # type: ignore[attr-defined]
                if not updated:
                    logger.warning(f"User with ID {entity_id} was not found.")
                else:
                    logger.info(f"User with ID {entity_id} updated successfully.")
                return updated
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Database error while updating user {entity_id}: {e}")
                raise DatabaseException(f"Failed to update user: {str(e)}") from e
            except Exception as e:
                await session.rollback()
                logger.error(
                    f"Unexpected error while updating user by ID {entity_id}: {e}"
                )
                raise DatabaseException(
                    f"Unexpected error while updating user by ID {entity_id}: {str(e)}"
                ) from e

    async def get_by_email(self, email: str) -> UserBase | None:
        """Gets the user entity from the database using e-mail address."""
        logger.info(f"Fetching user by email address {email} from the database...")
        try:
            async with self.async_session_maker() as session:
                query = select(UserBase).where(UserBase.email == email)
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                if user:
                    logger.info(f"Fetched user: {user}")
                else:
                    logger.warning(
                        f"User with provided e-mail address {email} not found."
                    )
                return user
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching user by email {email}: {e}")
            raise DatabaseException(
                f"Failed to fetch user by email {email}: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error while fetching user by email {email}: {e}")
            raise DatabaseException(
                f"Unexpected error while fetching user by email: {str(e)}"
            ) from e

    async def get_by_username(self, username: str) -> UserBase | None:
        """Gets the user entity from the database using username."""
        try:
            async with self.async_session_maker() as session:
                query = select(UserBase).where(UserBase.username == username)
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                return user
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while fetching user by username {username}: {e}"
            )
            raise DatabaseException(
                f"Failed to fetch user by username {username}: {str(e)}"
            ) from e
        except UserNotFoundException:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while fetching user by username {username}: {e}"
            )
            raise DatabaseException(
                f"Unexpected error while fetching user by username: {str(e)}"
            ) from e

    async def get_by_id(self, user_id: UUID) -> UserBase | None:
        """Gets the user entity from the database using user ID."""
        try:
            async with self.async_session_maker() as session:
                query = select(UserBase).where(UserBase.user_id == user_id)
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                return user
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching user by ID {user_id}: {e}")
            raise DatabaseException(
                f"Failed to fetch user by ID {user_id}: {str(e)}"
            ) from e
        except UserNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error while fetching user by ID {user_id}: {e}")
            raise DatabaseException(
                f"Unexpected error while fetching user by ID: {str(e)}"
            ) from e

    async def exists_by_email(self, email: str) -> bool:
        """Check if user entity exists by email."""
        user = await self.get_by_email(email)
        return user is not None

    async def exists_by_username(self, username: str) -> bool:
        """Check if user entity exists by username."""
        user = await self.get_by_username(username)
        return user is not None

    async def get_all(self) -> list[UserBase]:
        """Fetches all the users entities from the database. Admin usage only."""
        async with self.async_session_maker() as session:
            try:
                query = select(UserBase)
                result = await session.execute(query)
                all_users = result.scalars().all()
                return list(all_users)
            except SQLAlchemyError as e:
                logger.error(f"Database error while fetching all users: {e}")
                raise DatabaseException(f"Failed to fetch all users: {str(e)}") from e
            except Exception as e:
                logger.error(f"Unexpected error while fetching all users: {e}")
                raise DatabaseException(
                    f"Unexpected error while fetching all users: {str(e)}"
                ) from e
