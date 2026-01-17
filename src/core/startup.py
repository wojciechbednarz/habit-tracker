"""Application startup utilities."""

from config import settings
from src.core.exceptions import UserNotFoundException
from src.core.habit_async import AsyncUserManager
from src.core.models import UserBase, UserRole
from src.core.schemas import UserUpdate
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def _set_env_variables() -> tuple[str, str, str]:
    """Sets environment variables for the application"""
    admin_username = settings.ADMIN_USERNAME
    admin_email = settings.ADMIN_EMAIL
    admin_password = settings.ADMIN_PASSWORD
    return admin_username, admin_email, admin_password


async def _promote_user_to_admin(
    user_manager: AsyncUserManager, admin_username: str, user: UserBase
) -> None:
    """Promotes a user with admin privileges"""
    user = await user_manager.get_user_by_username(admin_username)
    logger.info(f"User '{admin_username}' exists, promoting to admin...")
    update = UserUpdate(role=UserRole.ADMIN)
    await user_manager.update_user(user.user_id, update)  # type: ignore[arg-type]
    logger.info(f"User '{admin_username}' promoted to admin")


async def ensure_admin_exists(user_manager: AsyncUserManager) -> None:
    """Ensures at least one admin user exists"""
    logger.info("Checking for existing admin users...")
    all_users = await user_manager.read_all_users()
    has_admin = any(user.role == UserRole.ADMIN for user in all_users)
    if not has_admin:
        admin_username, admin_email, admin_password = _set_env_variables()
        try:
            existing_user = await user_manager.get_user_by_username(admin_username)
            await _promote_user_to_admin(user_manager, admin_username, existing_user)
        except UserNotFoundException:
            new_user = await user_manager.create_user(
                username=admin_username,
                email=admin_email,
                nickname="Administrator",
                password=admin_password,
            )
            await _promote_user_to_admin(user_manager, admin_username, new_user)
    else:
        logger.info("Admin user already exists")
