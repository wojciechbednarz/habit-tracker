"""conftest.py - Pytest fixtures for habit tracker tests."""

import random
import uuid
from collections.abc import AsyncGenerator, Callable, Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from src.api.main import app
from src.api.v1.routers.dependencies import (
    get_current_active_user,
    get_current_user_with_role,
    get_habit_manager,
    get_user_manager,
    require_admin,
)
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


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Fast unit tests with mocks")
    config.addinivalue_line("markers", "integration: Integration tests with real DB")


# ==================== SHARED FIXTURES ====================


@pytest.fixture(scope="function")
def fake_user_data() -> tuple[str, str, str, str]:
    """Generate fake user data for testing, now including password."""
    faker = Faker()
    unique_suffix = str(uuid.uuid4())[:8]
    username = f"{faker.user_name()}-{unique_suffix}"
    email = f"{username}@example.com"
    nickname = faker.first_name()
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
def mock_sync_db(tmp_path: str) -> str:
    """Mocks a database where habits are stored"""
    test_db = "test_habits.db"
    test_db_url = tmp_path / test_db
    test_db_url = f"sqlite:///{test_db_url}"
    db = SyncDatabase(db_url=test_db_url)
    Base.metadata.create_all(bind=db.sync_engine)
    yield test_db_url
    db.sync_engine.dispose()


@pytest.fixture(scope="function")
def habit_manager(mock_sync_db: str) -> HabitManager:
    """Create HabitManager with isolated test database."""
    manager = HabitManager(db_path=mock_sync_db)
    yield manager
    manager.clear_all_habits()
    manager.service.db.sync_engine.dispose()


@pytest.fixture(scope="function")
def user_manager(mock_sync_db: str) -> UserManager:
    """Create HabitManager with isolated test database."""
    manager = UserManager(db_path=mock_sync_db)
    yield manager
    manager.user_service.db.sync_engine.dispose()


@pytest.fixture(scope="function")
def test_user(
    user_manager: UserManager,
    fake_user_data: tuple[str, str, str, str],
) -> AsyncGenerator[UserBase]:
    """Create a test user and return its content"""
    username, email, nickname, password = fake_user_data
    user = user_manager.create_user(
        username=username, email=email, nickname=nickname, password=password
    )
    user.password = password
    yield user
    try:
        user_manager.delete_user(user.user_id)
    except Exception:
        pass


@pytest.fixture()
def api_client(
    async_user_manager: AsyncUserManager, async_habit_manager: AsyncHabitManager
) -> Generator[TestClient]:
    """Test client with overridden dependencies."""
    app.dependency_overrides[get_user_manager] = lambda: async_user_manager
    app.dependency_overrides[get_habit_manager] = lambda: async_habit_manager
    with patch("src.api.main.ensure_admin_exists", new_callable=AsyncMock):
        with TestClient(app) as client:
            yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def mock_get_current_user_with_role(async_test_user_sqlite: UserBase) -> UserWithRole:
    """Mock fixture for getting the current user"""

    async def _mock_user() -> User:
        """Mock user inner function"""
        return UserWithRole(
            user_id=async_test_user_sqlite.user_id,
            username=async_test_user_sqlite.username,
            email=async_test_user_sqlite.email,
            nickname=async_test_user_sqlite.nickname,
            created_at=async_test_user_sqlite.created_at,
            disabled=False,
            role="user",
        )

    return _mock_user


@pytest.fixture()
def mock_get_current_active_user(async_test_user_sqlite: UserBase) -> Callable:
    """Mock fixture for getting the current active user"""

    async def _mock_user() -> User:
        """Mock user inner function"""
        return User(
            user_id=async_test_user_sqlite.user_id,
            username=async_test_user_sqlite.username,
            email=async_test_user_sqlite.email,
            nickname=async_test_user_sqlite.nickname,
            created_at=async_test_user_sqlite.created_at,
            disabled=False,
        )

    return _mock_user


@pytest.fixture()
def mock_require_admin(async_admin_user: UserBase) -> Callable:
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
    mock_get_current_user_with_role: UserWithRole,
    mock_get_current_active_user: User,
) -> Generator[TestClient]:
    """
    Test client with overridden dependencies.
    Mocked ensure_admin_exists, to not call db for default admin creation.
    """
    app.dependency_overrides[get_user_manager] = lambda: async_user_manager
    app.dependency_overrides[get_habit_manager] = lambda: async_habit_manager
    app.dependency_overrides[get_current_user_with_role] = (
        mock_get_current_user_with_role
    )
    app.dependency_overrides[get_current_active_user] = mock_get_current_active_user

    with patch("src.api.main.ensure_admin_exists", new_callable=AsyncMock):
        with TestClient(app) as client:
            yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def authenticated_as_admin_api_client(
    async_user_manager: AsyncUserManager,
    async_habit_manager: AsyncHabitManager,
    mock_require_admin: Callable,
) -> Generator[TestClient]:
    """
    Test client with overridden dependencies.
    Mocked ensure_admin_exists, to not call db for default admin creation.
    """
    app.dependency_overrides[get_user_manager] = lambda: async_user_manager
    app.dependency_overrides[get_habit_manager] = lambda: async_habit_manager
    app.dependency_overrides[require_admin] = mock_require_admin

    with patch("src.api.main.ensure_admin_exists", new_callable=AsyncMock):
        with TestClient(app) as client:
            yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def create_user_entity(
    fake_user_data_factory: Callable[[], tuple[str, str, str, str]],
) -> Callable[..., UserBase]:
    """Factory to create UserBase entity for testing."""

    def _create_user(**kwargs) -> UserBase:
        """Create a UserBase entity with optional overrides."""
        username, email, nickname, password = fake_user_data_factory()
        return UserBase(
            user_id=uuid4(),
            username=kwargs.get("username", username),
            email=kwargs.get("email", email),
            nickname=kwargs.get("nickname", nickname),
            created_at=datetime.now(UTC),
            disabled=False,
            hashed_password=get_password_hash(kwargs.get("password", password)),
        )

    return _create_user


@pytest.fixture()
def create_habit_entity(
    fake_habit_data_factory: Callable[[], tuple[str, str, str]],
) -> Callable[..., HabitBase]:
    """Factory to create HabitBase entity for testing."""

    def _create_habit(**kwargs) -> HabitBase:
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
def postgres_container() -> Generator:
    with PostgresContainer("postgres") as postgres:
        yield postgres


# ==================== ASYNC FIXTURES ====================


@pytest_asyncio.fixture()
async def mock_async_sqlite_db(tmp_path: str) -> AsyncGenerator[str]:
    """Mocks SQLite database"""
    test_db = "test_habits_async.db"
    test_db_url = tmp_path / test_db
    test_db_url = f"sqlite+aiosqlite:///{test_db_url}"
    db = AsyncDatabase(db_url=test_db_url)
    await db.init_db_async()
    yield test_db_url
    await db.async_engine.dispose()


@pytest_asyncio.fixture()
async def postgres_db_objects(postgres_container) -> AsyncGenerator[str, str]:
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
) -> AsyncGenerator[UserBase]:
    """
    Create a test user and return its content. Uses SQlite database.
    """
    username, email, nickname, password = fake_user_data
    user = await async_user_manager.create_user(
        username=username, email=email, nickname=nickname, password=password
    )
    user.password = password
    yield user
    try:
        await async_user_manager.delete_user(user.user_id)
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
    yield user
    try:
        await user_repository_real_db.delete(user.user_id)
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
    user.password = password
    update = UserUpdate(role="admin")
    await async_user_manager.update_user(user.user_id, update)
    user = await async_user_manager.get_user_by_email_address(user.email)
    yield user
    try:
        await async_user_manager.delete_user(user.user_id)
    except Exception:
        pass


@pytest_asyncio.fixture(scope="function")
async def async_test_habit(
    async_habit_manager: AsyncHabitManager,
    async_test_user_sqlite: UserBase,
    fake_habit_data_factory: Callable[[], tuple[str, str, str]],
) -> HabitBase:
    """Create a test user and return its content"""
    habit_name, description, frequency = fake_habit_data_factory()
    habit = await async_habit_manager.add_habit(
        user_id=async_test_user_sqlite.user_id,
        habit_name=habit_name,
        description=description,
        frequency=frequency,
    )
    return habit


@pytest_asyncio.fixture(scope="function")
async def async_test_habits(
    async_habit_manager: AsyncHabitManager,
    async_test_user_sqlite: UserBase,
    fake_habit_data_factory: Callable[[], tuple[str, str, str]],
) -> list[HabitBase]:
    """Create multiple test habits for a user and return their content"""
    habits = []
    for _ in range(5):
        habit_name, description, frequency = fake_habit_data_factory()
        habit = await async_habit_manager.add_habit(
            user_id=async_test_user_sqlite.user_id,
            habit_name=habit_name,
            description=description,
            frequency=frequency,
        )
        habits.append(habit)
    return habits


@pytest_asyncio.fixture
async def mocked_async_session_maker() -> Callable:
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
async def mocked_user_repository():
    """
    Mocks the UserRepository class.
    Unit testing purpose (service layer).
    """
    return AsyncMock(spec=UserRepository)


@pytest_asyncio.fixture()
async def mocked_habit_repository():
    """
    Mocks the HabitRepository class.
    Unit testing purpose (service layer).
    """
    return AsyncMock(spec=HabitRepository)


@pytest_asyncio.fixture()
async def user_repository_real_db(postgres_db_objects: AsyncGenerator):
    """
    Mocks the UserRepository class.
    Integration testing purpose (API and repository layers).
    """
    postgres_session_maker, _ = postgres_db_objects
    user_repo = UserRepository(postgres_session_maker)
    yield user_repo


@pytest_asyncio.fixture()
async def habit_repository_real_db(postgres_db_objects: AsyncGenerator):
    """
    Mocks the HabitRepository class.
    Integration testing purpose (API and repository layers).
    """
    postgres_session_maker, async_engine = postgres_db_objects
    habit_repo = HabitRepository(postgres_session_maker, async_engine)
    yield habit_repo


@pytest_asyncio.fixture
async def mocked_habit_service(mocked_habit_repository, mocked_user_repository):
    """Create real AsyncHabitService with mocked repositories."""
    mock_db = AsyncMock(spec=AsyncDatabase)
    mock_db.async_session_maker = AsyncMock()
    mock_db.async_engine = AsyncMock()
    return AsyncHabitService(mocked_user_repository, mocked_habit_repository, mock_db)


@pytest_asyncio.fixture
async def mocked_user_service(
    mocked_async_session_maker, mocked_habit_repository, mocked_user_repository
):
    """Create real AsyncUserService with mocked repositories."""
    mock_db = AsyncMock(spec=AsyncDatabase)
    mock_db.async_session_maker = mocked_async_session_maker
    mock_db.async_engine = AsyncMock()
    service = AsyncUserService(mocked_user_repository, mocked_habit_repository, mock_db)
    service._mock_session = mocked_async_session_maker.return_value
    return service


@pytest_asyncio.fixture
async def mocked_habit_manager(mocked_habit_service):
    """Create real AsyncHabitManager with mocked service layer."""
    return AsyncHabitManager(service=mocked_habit_service)


@pytest_asyncio.fixture
async def mocked_user_manager(mocked_user_service):
    """Create real AsyncUserManager with mocked service layer."""
    return AsyncUserManager(service=mocked_user_service)
