"""conftest.py - Pytest fixtures for habit tracker tests."""

import random
import uuid
from collections.abc import AsyncGenerator, Callable, Coroutine, Generator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from faker import Faker
from fastapi import FastAPI
from fastapi.testclient import TestClient
from redis.asyncio import Redis, RedisError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from src.api.main import app
from src.api.v1.routers.dependencies import (
    get_current_active_user,
    get_current_user_with_role,
    get_habit_manager,
    get_user_manager,
    require_admin,
)
from src.core.cache import RedisManager
from src.core.db import AsyncDatabase, SyncDatabase
from src.core.habit import HabitManager, UserManager
from src.core.habit_async import (
    AsyncHabitManager,
    AsyncHabitService,
    AsyncUserManager,
    AsyncUserService,
)
from src.core.models import Base, HabitBase, UserBase
from src.core.schemas import User, UserUpdate, UserWithRole
from src.core.security import get_password_hash
from src.repository.habit_repository import HabitRepository
from src.repository.user_repository import UserRepository


def pytest_configure(config: Any) -> None:
    """Pytest configuration method"""
    config.addinivalue_line("markers", "unit: Fast unit tests with mocks")
    config.addinivalue_line("markers", "integration: Integration tests with real DB")


# ==================== SHARED FIXTURES ====================


@pytest.fixture(scope="function")
def fake_user_data() -> tuple[str, str, str, str]:
    """Generate fake user data for testing."""
    faker = Faker()
    unique_suffix = str(uuid.uuid4())[:8]
    username = f"{faker.user_name()}-{unique_suffix}"
    email = f"{username}@example.com"
    nickname = f"{faker.first_name()}-{unique_suffix}"
    password = faker.password(length=10)
    return username, email, nickname, password


@pytest.fixture(scope="function")
def fake_habit_data_factory() -> Callable[[], tuple[str, str, str]]:
    """Factory to generate unique habit data."""

    def _make_habit_data() -> tuple[str, str, str]:
        faker = Faker()
        unique_suffix = str(uuid.uuid4())[:8]
        habit_name = f"{faker.word().capitalize()}-{unique_suffix}"
        description = faker.sentence()
        frequency = random.choice(["daily", "weekly", "monthly"])
        return habit_name, description, frequency

    return _make_habit_data


@pytest.fixture(scope="function")
def fake_user_data_factory() -> Callable[[], tuple[str, str, str, str]]:
    """Factory to generate unique user data on each call."""

    def _make_user_data() -> tuple[str, str, str, str]:
        faker = Faker()
        unique_suffix = str(uuid.uuid4())[:8]
        username = f"{faker.user_name()}-{unique_suffix}"
        email = f"{username}@example.com"
        nickname = faker.first_name()
        password = faker.password(length=10)
        return username, email, nickname, password

    return _make_user_data


# ==================== SYNC FIXTURES ====================


@pytest.fixture()
def mock_sync_db(tmp_path: Path) -> Generator[str]:
    """Mocks a database where habits are stored"""
    test_db = "test_habits.db"
    test_db_path = tmp_path / test_db
    db_url_str = f"sqlite:///{test_db_path}"
    db = SyncDatabase(db_url=db_url_str)
    Base.metadata.create_all(bind=db.sync_engine)
    yield db_url_str
    db.sync_engine.dispose()


@pytest.fixture(scope="function")
def habit_manager(mock_sync_db: str) -> Generator[HabitManager]:
    """Create HabitManager with isolated test database."""
    manager = HabitManager(db_path=mock_sync_db)
    yield manager
    manager.clear_all_habits()
    manager.service.db.sync_engine.dispose()


@pytest.fixture(scope="function")
def user_manager(mock_sync_db: str) -> Generator[UserManager]:
    """Create HabitManager with isolated test database."""
    manager = UserManager(db_path=mock_sync_db)
    yield manager
    manager.user_service.db.sync_engine.dispose()


@pytest.fixture()
def api_client(
    async_user_manager: AsyncUserManager,
    async_habit_manager: AsyncHabitManager,
    test_lifespan: Callable[Redis],
) -> Generator[TestClient]:
    """
    Test client with overridden dependencies and without user or admin authorization.
    'test_lifespan' fixture handles RedisManager instance via lifespan events from
    FastAPI.
    """
    app.router.lifespan_context = test_lifespan
    app.dependency_overrides[get_user_manager] = lambda: async_user_manager
    app.dependency_overrides[get_habit_manager] = lambda: async_habit_manager
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def mock_get_current_user_with_role(
    async_test_user_sqlite: dict[str, Any],
) -> Callable[[], Coroutine[Any, Any, UserWithRole]]:
    """Mock fixture for getting the current user"""

    async def _mock_user() -> UserWithRole:
        """Mock user inner function"""
        user = async_test_user_sqlite["user"]
        return UserWithRole(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            nickname=user.nickname,
            created_at=user.created_at,
            disabled=False,
            role="user",
        )

    return _mock_user


@pytest.fixture()
def mock_get_current_active_user(
    async_test_user_sqlite: dict[str, Any],
) -> Callable[[], Coroutine[Any, Any, User]]:
    """Mock fixture for getting the current active user"""

    async def _mock_user() -> User:
        """Mock user inner function"""
        user = async_test_user_sqlite["user"]
        return User(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            nickname=user.nickname,
            created_at=user.created_at,
            disabled=False,
        )

    return _mock_user


@pytest.fixture()
def mock_require_admin(
    async_admin_user: UserBase,
) -> Callable[[], Coroutine[Any, Any, UserWithRole]]:
    """Mock fixture for getting admin user"""

    async def _mock_user() -> UserWithRole:
        """Mock user with role function"""
        return UserWithRole(
            user_id=async_admin_user.user_id,
            username=async_admin_user.username,
            email=async_admin_user.email,
            nickname=async_admin_user.nickname,
            created_at=async_admin_user.created_at,
            disabled=False,
            role="admin",
        )

    return _mock_user


@pytest.fixture()
def authenticated_as_user_api_client(
    async_user_manager: AsyncUserManager,
    async_habit_manager: AsyncHabitManager,
    test_lifespan: Callable[Redis],
    mock_get_current_user_with_role: Callable[[], Coroutine[Any, Any, UserWithRole]],
    mock_get_current_active_user: Callable[[], Coroutine[Any, Any, User]],
) -> Generator[TestClient]:
    """
    Test client with overridden dependencies with user authorization.
    'test_lifespan' fixture handles RedisManager instance via lifespan events from
    FastAPI.
    """
    app.router.lifespan_context = test_lifespan
    app.dependency_overrides[get_user_manager] = lambda: async_user_manager
    app.dependency_overrides[get_habit_manager] = lambda: async_habit_manager
    app.dependency_overrides[get_current_user_with_role] = (
        mock_get_current_user_with_role
    )
    app.dependency_overrides[get_current_active_user] = mock_get_current_active_user
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def authenticated_as_admin_api_client(
    async_user_manager: AsyncUserManager,
    async_habit_manager: AsyncHabitManager,
    test_lifespan: Callable[Redis],
    mock_require_admin: Callable[[], Coroutine[Any, Any, UserWithRole]],
) -> Generator[TestClient]:
    """
    Test client with overridden dependencies authenticated as admin.
    'test_lifespan' fixture handles RedisManager instance via lifespan events from
    FastAPI.
    """
    app.router.lifespan_context = test_lifespan
    app.dependency_overrides[get_user_manager] = lambda: async_user_manager
    app.dependency_overrides[get_habit_manager] = lambda: async_habit_manager
    app.dependency_overrides[require_admin] = mock_require_admin
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def create_user_entity(
    fake_user_data_factory: Callable[[], tuple[str, str, str, str]],
) -> Callable[..., UserBase]:
    """Factory to create UserBase entity for testing."""

    def _create_user(**kwargs: Any) -> UserBase:  # Changed from dict[str, Any]
        """Create a UserBase entity with optional overrides."""
        username, email, nickname, password = fake_user_data_factory()
        password_value = kwargs.get("password", password)
        if not isinstance(password_value, str):
            raise ValueError("Password must be a string")

        return UserBase(
            user_id=uuid4(),
            username=kwargs.get("username", username),
            email=kwargs.get("email", email),
            nickname=kwargs.get("nickname", nickname),
            created_at=datetime.now(UTC),
            disabled=False,
            hashed_password=get_password_hash(password_value),
        )

    return _create_user


@pytest.fixture()
def create_habit_entity(
    fake_habit_data_factory: Callable[[], tuple[str, str, str]],
) -> Callable[..., HabitBase]:
    """Factory to create HabitBase entity for testing."""

    def _create_habit(**kwargs: Any) -> HabitBase:  # Changed from dict[str, Any]
        """Create a HabitBase entity with optional overrides."""
        habit_name, description, frequency = fake_habit_data_factory()
        return HabitBase(
            id=uuid4(),
            user_id=kwargs.get("user_id", uuid4()),
            name=kwargs.get("name", habit_name),
            description=kwargs.get("description", description),
            frequency=kwargs.get("frequency", frequency),
            mark_done=kwargs.get("mark_done", False),
            created_at=datetime.now(UTC),
        )

    return _create_habit


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer]:
    """Creates a postgres container"""
    with PostgresContainer("postgres") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def redis_container() -> Generator[RedisContainer]:
    """Creates a redis container"""
    with RedisContainer("redis:8.4.0-alpine") as redis:
        yield redis


# @pytest.fixture(scope="function")
# def test_lifespan(redis_manager: RedisManager) -> Callable:
#     """Factory that creates a test lifespan context manager."""
#     @asynccontextmanager
#     async def _test_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
#         """Test lifespan that uses test Redis."""
#         app.state.redis_manager = redis_manager
#         yield
#     return _test_lifespan


@pytest.fixture()
def test_lifespan(redis_instance: str) -> Callable[[FastAPI], Any]:
    """Factory that creates a test lifespan context manager. test_habit_api.py usage"""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        """Test lifespan that uses test Redis."""
        redis_client = await Redis.from_url(redis_instance, decode_responses=True)
        manager = RedisManager()
        await manager.initialize(redis_instance)
        app.state.redis_manager = manager
        yield
        await manager.close()
        await redis_client.aclose()  # type: ignore[attr-defined]

    return lifespan


# ==================== ASYNC FIXTURES ====================


@pytest_asyncio.fixture()
async def mock_async_sqlite_db(tmp_path: Path) -> AsyncGenerator[str]:
    """Mocks SQLite database"""
    test_db = "test_habits_async.db"
    test_db_path = tmp_path / test_db
    test_db_url = f"sqlite+aiosqlite:///{test_db_path}"
    db = AsyncDatabase(db_url=test_db_url)
    await db.init_db_async()
    yield test_db_url
    await db.async_engine.dispose()


@pytest_asyncio.fixture()
async def postgres_db_objects(
    postgres_container: PostgresContainer,
) -> AsyncGenerator[tuple[async_sessionmaker[AsyncSession], AsyncEngine]]:
    """
    Mocks postgres database. Integration tests for real db purpose.
    """
    db_url = postgres_container.get_connection_url().replace(
        "postgresql+psycopg2://", "postgresql+asyncpg://"
    )
    print(f"DB URL--------- {db_url}")
    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    yield async_session, engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture()
async def redis_instance(redis_container: RedisContainer) -> AsyncGenerator[str]:
    """Sets up redis connection URL. test_cache_redis.py usage"""
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(redis_container.port)
    full_url = f"redis://{host}:{port}"
    yield full_url


@pytest_asyncio.fixture()
async def redis_client(redis_instance: str) -> AsyncGenerator[Redis[str]]:
    """Sets up connection to Redis client. test_cache_redis.py usage"""
    client = await Redis.from_url(redis_instance, decode_responses=True)
    try:
        await client.ping()
    except RedisError as e:
        pytest.fail(f"Failed to connect to Redis: {e}")
    yield client
    await client.flushall()
    await client.close()


@pytest_asyncio.fixture()
async def cache_manager(redis_client: Redis[str]) -> AsyncGenerator[RedisManager]:
    """Creates a RedisManager instance and uses Redis client from testcontainers"""
    cache = RedisManager(redis_client)
    yield cache


@pytest_asyncio.fixture(scope="function")
async def async_user_manager(
    mock_async_sqlite_db: str,
) -> AsyncGenerator[AsyncUserManager]:
    """Create UserManager with async database for API tests."""
    user_manager = AsyncUserManager(db_path=mock_async_sqlite_db)
    yield user_manager
    await user_manager.service.async_db.async_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_habit_manager(
    mock_async_sqlite_db: str,
) -> AsyncGenerator[AsyncHabitManager]:
    habit_manager = AsyncHabitManager(db_path=mock_async_sqlite_db)
    yield habit_manager
    await habit_manager.async_db.async_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_test_user_sqlite(
    async_user_manager: AsyncUserManager,
    fake_user_data: tuple[str, str, str, str],
) -> AsyncGenerator[dict[str, Any]]:
    """
    Create a test user and return its content. Uses SQlite database.
    """
    username, email, nickname, password = fake_user_data
    user = await async_user_manager.create_user(
        username=username, email=email, nickname=nickname, password=password
    )
    # Store the actual user_id as UUID type
    user_id: UUID = user.user_id  # type: ignore[assignment]
    user.hashed_password = get_password_hash(password)  # type: ignore[assignment]
    yield {"user": user, "password": password}
    try:
        await async_user_manager.delete_user(user_id)
    except Exception:
        pass


@pytest_asyncio.fixture(scope="function")
async def async_test_user_postgres(
    user_repository_real_db: UserRepository, create_user_entity: Callable[..., UserBase]
) -> AsyncGenerator[UserBase]:
    """
    Create a test user and return its content. Uses postgres database.
    """
    user = await user_repository_real_db.add(create_user_entity())
    user_id: UUID = user.user_id  # type: ignore[assignment]
    yield user
    try:
        await user_repository_real_db.delete(user_id)
    except Exception:
        pass


@pytest_asyncio.fixture(scope="function")
async def async_admin_user(
    async_user_manager: AsyncUserManager,
    fake_user_data_factory: Callable[[], tuple[str, str, str, str]],
) -> AsyncGenerator[UserBase]:
    """Create a test admin user"""
    username, email, nickname, password = fake_user_data_factory()
    user = await async_user_manager.create_user(
        username=username, email=email, nickname=nickname, password=password
    )
    user_id: UUID = user.user_id  # type: ignore[assignment]
    user_email: str = user.email  # type: ignore[assignment]
    user.hashed_password = get_password_hash(password)  # type: ignore[assignment]
    update = UserUpdate(role="admin")
    await async_user_manager.update_user(user_id, update)
    user = await async_user_manager.get_user_by_email_address(user_email)
    yield user
    try:
        await async_user_manager.delete_user(user_id)
    except Exception:
        pass


@pytest_asyncio.fixture(scope="function")
async def async_test_habit(
    async_habit_manager: AsyncHabitManager,
    async_test_user_sqlite: dict[str, Any],
    fake_habit_data_factory: Callable[[], tuple[str, str, str]],
) -> HabitBase:
    """Create a test user and return its content"""
    habit_name, description, frequency = fake_habit_data_factory()
    user_id: UUID = async_test_user_sqlite["user"].user_id
    habit = await async_habit_manager.add_habit(
        user_id=user_id,
        habit_name=habit_name,
        description=description,
        frequency=frequency,
    )
    return habit


@pytest_asyncio.fixture(scope="function")
async def async_test_habits(
    async_habit_manager: AsyncHabitManager,
    async_test_user_sqlite: dict[str, Any],
    fake_habit_data_factory: Callable[[], tuple[str, str, str]],
) -> list[HabitBase]:
    """Create multiple test habits for a user and return their content"""
    habits = []
    user_id: UUID = async_test_user_sqlite["user"].user_id
    for _ in range(5):
        habit_name, description, frequency = fake_habit_data_factory()
        habit = await async_habit_manager.add_habit(
            user_id=user_id,
            habit_name=habit_name,
            description=description,
            frequency=frequency,
        )
        habits.append(habit)
    return habits


@pytest_asyncio.fixture
async def mocked_async_session_maker() -> Callable[..., AsyncSession]:
    """
    Mocks async_sessionmaker and its methods.
    Unit testing purpose (service layer).
    """
    session = AsyncMock(spec=AsyncSession)
    session.__aenter__.return_value = session
    session.__aexit__.return_value = None
    session.add = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()

    mock_session_maker = MagicMock()
    mock_session_maker.return_value = session
    return mock_session_maker


@pytest_asyncio.fixture()
async def mocked_user_repository() -> AsyncMock:
    """
    Mocks the UserRepository class.
    Unit testing purpose (service layer).
    """
    return AsyncMock(spec=UserRepository)


@pytest_asyncio.fixture()
async def mocked_habit_repository() -> AsyncMock:
    """
    Mocks the HabitRepository class.
    Unit testing purpose (service layer).
    """
    return AsyncMock(spec=HabitRepository)


@pytest_asyncio.fixture()
async def user_repository_real_db(
    postgres_db_objects: tuple[async_sessionmaker[AsyncSession], AsyncEngine],
) -> AsyncGenerator[UserRepository]:
    """
    Mocks the UserRepository class.
    Integration testing purpose (API and repository layers).
    """
    postgres_session_maker, _ = postgres_db_objects
    user_repo = UserRepository(postgres_session_maker)
    yield user_repo


@pytest_asyncio.fixture()
async def habit_repository_real_db(
    postgres_db_objects: tuple[async_sessionmaker[AsyncSession], AsyncEngine],
) -> AsyncGenerator[HabitRepository]:
    """
    Mocks the HabitRepository class.
    Integration testing purpose (API and repository layers).
    """
    postgres_session_maker, async_engine = postgres_db_objects
    habit_repo = HabitRepository(postgres_session_maker, async_engine)
    yield habit_repo


@pytest_asyncio.fixture
async def mocked_habit_service(
    mocked_habit_repository: AsyncMock, mocked_user_repository: AsyncMock
) -> AsyncHabitService:
    """Create real AsyncHabitService with mocked repositories."""
    mock_db = AsyncMock(spec=AsyncDatabase)
    mock_db.async_session_maker = AsyncMock()
    mock_db.async_engine = AsyncMock()
    return AsyncHabitService(mocked_user_repository, mocked_habit_repository, mock_db)


@pytest_asyncio.fixture
async def mocked_user_service(
    mocked_async_session_maker: Callable[..., AsyncSession],
    mocked_habit_repository: AsyncMock,
    mocked_user_repository: AsyncMock,
) -> AsyncUserService:
    """Create real AsyncUserService with mocked repositories."""
    mock_db = AsyncMock(spec=AsyncDatabase)
    mock_db.async_session_maker = mocked_async_session_maker
    mock_db.async_engine = AsyncMock()
    service = AsyncUserService(mocked_user_repository, mocked_habit_repository, mock_db)
    service._mock_session = mocked_async_session_maker.return_value  # type: ignore[attr-defined]
    return service


@pytest_asyncio.fixture
async def mocked_habit_manager(
    mocked_habit_service: AsyncHabitService,
) -> AsyncHabitManager:
    """Create real AsyncHabitManager with mocked service layer."""
    return AsyncHabitManager(service=mocked_habit_service)


@pytest_asyncio.fixture
async def mocked_user_manager(
    mocked_user_service: AsyncUserService,
) -> AsyncUserManager:
    """Create real AsyncUserManager with mocked service layer."""
    return AsyncUserManager(service=mocked_user_service)
