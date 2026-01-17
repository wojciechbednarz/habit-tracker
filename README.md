# Habit Tracker

**Version 0.2.0**

A command-line application for tracking daily habits with per-user support and PostgreSQL persistence.

## Features

- **Per-user habit management** with JWT authentication and password hashing
- **REST API** built with FastAPI for habit tracking operations
- **CLI interface** with interactive and command-line modes
- **Add, complete, and list habits** with custom descriptions and frequencies
- **SQlite database** for quick unit tests
- **PostgreSQL database** with SQLAlchemy ORM (async support)
- **Alembic database migrations** for schema management
- **Type-safe operations** with Pydantic validation
- **Comprehensive test coverage** with pytest
- **Repository pattern** for data access layer
- **Security features** password hashing (pwdlib), JWT tokens
- **Containerization** with Docker containers

## Requirements

- Python 3.13+
- uv (recommended for dependency management)

## Key Dependencies

- FastAPI 0.121.1+ - Web framework for API
- SQLAlchemy 2.0.44+ - ORM with async support
- Alembic 1.17.2+ - Database migrations
- Pydantic 2.12.4+ - Data validation
- PyJWT 2.10.1+ - JWT token handling
- pwdlib 0.3.0+ - Password hashing
- pytest 8.4.2+ - Testing framework
- Ruff 0.14.4+ - Linting and formatting
- mypy 1.18.2+ - Type checking

## Installation

```bash
git clone https://github.com/wojciechbednarz/habit-tracker.git
cd habit-tracker
uv sync
```

## Usage

### Interactive Mode

```bash
uv run python -m src.cli.main interactive
```

On startup, you will be prompted for a username. If the user does not exist, you will be asked to provide an email and nickname to create a new account.

Available commands in interactive mode:
- `add` - Add a new habit (prompts for name, description, frequency)
- `complete` - Mark a habit as complete
- `list` - Display all habits for the current user
- `quit` - Exit interactive mode

### Command-Line Mode

```bash
# Add a habit
uv run python -m src.cli.main add --name "Morning Exercise" --description "Daily exercise routine" --frequency daily

# Mark a habit as complete (use the habit name as argument)
uv run python -m src.cli.main complete "Morning Exercise"

# List all habits
uv run python -m src.cli.main list-all
```

### API Mode

Start the FastAPI server:

```bash
uv run uvicorn src.api.main:app --reload
```

The API will be available at `http://localhost:8000` with interactive docs at `/docs`.

**API Endpoints:**
- `POST /api/v1/users/` - Create new user
- `POST /api/v1/security/token` - Get JWT access token
- `GET /api/v1/habits/` - List user's habits
- `POST /api/v1/habits/` - Create new habit
- `PUT /api/v1/habits/{habit_id}` - Update habit
- `DELETE /api/v1/habits/{habit_id}` - Delete habit
- `POST /api/v1/habits/{habit_id}/complete` - Mark habit as complete

## Project Structure

```
habit-tracker/
├── alembic/                 # Database migrations
│   ├── versions/           # Migration scripts
│   ├── env.py
│   └── script.py.mako
├── src/
│   ├── api/                # FastAPI REST API
│   │   ├── main.py        # API entry point
│   │   └── v1/            # API version 1
│   │       └── routers/   # API route handlers
│   │           ├── admin.py
│   │           ├── dependencies.py
│   │           ├── habits.py
│   │           ├── security.py
│   │           └── users.py
│   ├── cli/                # Command-line interface
│   │   ├── commands.py    # CLI commands
│   │   └── main.py        # CLI entry point
│   ├── core/               # Core business logic
│   │   ├── db.py          # Database session management
│   │   ├── exceptions.py  # Custom exceptions
│   │   ├── greet.py       # Greeting functionality
│   │   ├── habit.py       # Habit management logic
│   │   ├── habit_async.py # Async habit operations
│   │   ├── models.py      # SQLAlchemy ORM models
│   │   ├── schemas.py     # Pydantic schemas
│   │   └── security.py    # Authentication & JWT
│   ├── repository/         # Data access layer
│   │   ├── base.py        # Base repository
│   │   ├── habit_repository.py
│   │   └── user_repository.py
│   └── utils/             # Utilities
│       ├── helpers.py
│       └── logger.py
├── tests/                  # Test suite
│   ├── test_habit_api.py
│   ├── test_habit_history.py
│   ├── test_habit_manager.py
│   ├── test_habit_repository.py
│   ├── test_habit_service.py
│   ├── test_habit_update.py
│   └── test_user_repository.py
├── alembic.ini
├── conftest.py             # Pytest fixtures
├── justfile                # Command shortcuts (just)
└── pyproject.toml          # Project configuration
```

## Development

### Setup

Install development dependencies:
```bash
uv sync
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html --cov-report=term

# Run specific test case with additional logging
uv run pytest -v -s -k "test_create_habit_positive"

# You can also use specific tag for given tests
uv run pytest -m unit

uv run pytest -m integration

# Or use justfile shortcuts
just test
just test-cov
```

### Code Quality

```bash
# Format code
just fmt

# Lint code
just lint

# Type check
just typecheck
```

### Database

The application itself uses dockerized PostgreSQL (also for integration tests) and SQLite (`habits.db`) for quick unit tests with async support via aiosqlite. Database schema is managed via Alembic migrations.

**Create a new migration:**
```bash
uv run alembic revision --autogenerate -m "Description"
```

**Apply migrations:**
```bash
uv run alembic upgrade head
```

**Rollback migration:**
```bash
uv run alembic downgrade -1
```


### Docker

The application is containerized using Docker. Dockerfile is created to run the app and used together with postgres and adminer services in `docker-compose.yaml`

# Run application and database services
```bash
docker-compose up
```

# Access the app via:
- http://127.0.0.1:8000

# Access the database via adminer:
- http://127.0.0.1:8080

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## License

This project is open source and available under the MIT License.

## Author

Wojciech Bednarz

Project Link: [https://github.com/wojciechbednarz/habit-tracker](https://github.com/wojciechbednarz/habit-tracker)
