# Habit Tracker

[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121%2B-009485)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-336791)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Version 0.1.0** | [Report Bug](https://github.com/wojciechbednarz/habit-tracker/issues) | [Request Feature](https://github.com/wojciechbednarz/habit-tracker/issues)

A production-grade, scalable habit tracking platform featuring real-time analytics, AI-powered coaching, asynchronous task processing, and intelligent caching. Built with modern Python architecture principles and enterprise-grade infrastructure.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Development](#development)
- [Performance & Scalability](#performance--scalability)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

Habit Tracker is a comprehensive habit management system designed for individuals seeking to build and maintain positive behavioral patterns. The platform combines behavioral psychology principles with modern software engineering to deliver an intuitive, scalable solution.

### Key Value Propositions

- **Intelligent Habit Coaching**: AI-powered recommendations using Ollama LLM integration
- **Real-time Analytics**: Weekly habit completion reports with PDF generation
- **Asynchronous Processing**: Non-blocking task handling via AWS SQS integration
- **Performance Optimized**: Redis caching for frequently accessed data
- **Type-Safe**: End-to-end type hints with mypy validation (163 → 92 errors fixed)
- **Comprehensive Testing**: Unit, integration, and end-to-end test coverage

## Features

### Core Functionality
- **Multi-user Habit Management** with granular access control and user isolation
- **Enterprise Security** with JWT tokens, password hashing (pwdlib), and role-based access
- **Advanced Analytics** including weekly habit statistics and PDF report generation
- **AI-Powered Coaching** via Ollama LLM for personalized habit advice
- **Smart Notifications** using AWS SES for email delivery and user engagement
- **Cloud Infrastructure** with AWS S3, SQS, and CloudFormation integration

### Technical Excellence
- **Fully Asynchronous** - Async/await throughout with non-blocking I/O operations
- **Type-Safe Operations** - Full Pydantic v2 validation with strict mypy checking
- **Repository Pattern** - Clean data access layer with abstraction
- **Intelligent Caching** - Redis-backed caching with TTL management
- **Production Database** - PostgreSQL with SQLAlchemy 2.0 ORM
- 🧪 **Comprehensive Testing** - Unit, integration, and E2E tests with testcontainers

### Developer Experience
- **Multiple Interfaces** - REST API, CLI (interactive & command-line), and programmatic access
- **Full Documentation** - Interactive API docs (Swagger/OpenAPI)
- **Development Tools** - Ruff formatting/linting, mypy type checking, pytest with coverage
- **Containerized** - Docker support for isolated, reproducible environments
- **Dependency Management** - Modern dependency resolution with uv

## Architecture

The application follows a **layered hexagonal architecture** pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                      │
│  (FastAPI Routes, CLI, WebSocket, REST Endpoints)           │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                     Dependency Injection                      │
│  (FastAPI Depends, Service Locator, Factory Patterns)       │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                    Business Logic Layer                       │
│  (Services, Use Cases, Domain Models, Event Handlers)       │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                     Data Access Layer                         │
│  (Repository Pattern, SQLAlchemy ORM, Query Builders)       │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                  Infrastructure Layer                         │
│  (PostgreSQL, Redis, AWS Services, Email, PDF Generation)   │
└─────────────────────────────────────────────────────────────┘
```

### Design Patterns Implemented

- **Repository Pattern**: Abstracted data access with `HabitRepository` and `UserRepository`
- **Dependency Injection**: FastAPI `Depends()` for service composition and testing
- **Event-Driven Architecture**: Habit completion, achievement unlocking, and notification events
- **Service Locator**: Centralized dependency management via context objects
- **Factory Pattern**: Fixture factories for test data generation
- **Mixin Pattern**: Reusable behavior composition in models

## Technology Stack

### Backend Framework
- **FastAPI 0.121.1+** - Modern ASGI web framework with async support
- **Uvicorn** - High-performance ASGI server implementation
- **Pydantic v2** - Data validation and serialization engine

### Database & ORM
- **PostgreSQL 15+** - Primary relational database
- **SQLAlchemy 2.0.44+** - Async-capable ORM with type hints
- **Alembic 1.17.2+** - Database versioning and migrations
- **asyncpg** - Async PostgreSQL driver

### Caching & Session Management
- **Redis 7.1.0+** - In-memory data store for caching and sessions
- **redis-py** - Python Redis client with async support

### Authentication & Security
- **PyJWT 2.10.1+** - JWT token handling and validation
- **pwdlib 0.3.0+** - Password hashing and verification
- **python-multipart** - Form data parsing

### AI & Machine Learning
- **Ollama** - Local LLM inference engine for habit coaching
- **httpx** - Async HTTP client for Ollama integration

### Cloud & Infrastructure
- **aioboto3** - Async AWS SDK (S3, SQS, SES, CloudFormation)
- **Jinja2** - Template rendering for HTML reports
- **WeasyPrint/reportlab** - PDF generation

### Development & Quality Assurance
- **pytest 8.4.2+** - Test framework with async support
- **pytest-asyncio** - Pytest plugin for async test functions
- **testcontainers 4.14.0+** - Containerized testing infrastructure
- **Ruff 0.14.4+** - Fast Python linter and formatter
- **mypy 1.18.2+** - Static type checker (92 errors fixed)
- **coverage** - Code coverage measurement

### Containerization & DevOps
- **Docker** - Application containerization
- **Docker Compose** - Multi-container orchestration
- **Trivy** - Security scanning for container images

## Requirements

### System Requirements
- **Python**: 3.13 or higher
- **Operating System**: Linux, macOS, or Windows (with WSL2)
- **Memory**: Minimum 2GB RAM recommended
- **Storage**: 5GB for development environment with Docker

### Dependencies Management
- **uv**: Modern Python package manager (recommended)
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### External Services (Optional)
- **PostgreSQL 15+**: Database server (or use Docker)
- **Redis 7.0+**: Caching layer (or use Docker)
- **AWS Account**: For cloud features (S3, SQS, SES)
- **Ollama**: For AI coaching features

## Installation

### Quick Start with Docker

The fastest way to get started:

```bash
# Clone repository
git clone https://github.com/wojciechbednarz/habit-tracker.git
cd habit-tracker

# Start application with all services
docker-compose up --build

# Application available at: http://localhost:8000
# Interactive API docs at: http://localhost:8000/docs
# Database UI (Adminer) at: http://localhost:8080
```

### Local Development Installation

#### 1. Clone Repository
```bash
git clone https://github.com/wojciechbednarz/habit-tracker.git
cd habit-tracker
```

#### 2. Set Up Python Environment
```bash
# Using uv (recommended)
uv python install 3.13
uv venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
# Using uv
uv sync

# Or using pip
pip install -r requirements.txt
```

#### 4. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit with your settings
nano .env
```

### Prerequisites for Development

#### PostgreSQL (Local or Docker)
```bash
# Using Docker
docker run --name habit-db \
  -e POSTGRES_PASSWORD=dev \
  -e POSTGRES_DB=habit_tracker \
  -p 5432:5432 \
  -d postgres:15-alpine

# Or use system PostgreSQL
# macOS: brew install postgresql
# Linux: sudo apt-get install postgresql
# Windows: Download from postgresql.org
```

#### Redis (Local or Docker)
```bash
# Using Docker
docker run --name habit-cache \
  -p 6379:6379 \
  -d redis:7-alpine

# Or use system Redis
# macOS: brew install redis
# Linux: sudo apt-get install redis-server
```

#### Ollama (for AI features)
```bash
# Download and install from https://ollama.ai
# Then pull the required model
ollama pull llama2:latest

# Start Ollama service (usually runs as daemon)
ollama serve
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/habit_tracker
DATABASE_ECHO=false  # Set to true for SQL query logging

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=3600

# Security
JWT_SECRET_KEY=your-secret-key-min-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
PASSWORD_HASH_ALGORITHM=bcrypt

# CORS Settings
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# Logging
LOG_LEVEL=INFO
LOGDIR=./logs

# AWS Configuration (optional)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_SQS_STACK_NAME=habit-tracker-sqs
AWS_SES_SENDER_EMAIL=noreply@habittracker.com

# Ollama Configuration (optional)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2:latest
OLLAMA_TIMEOUT=30
```

### Database Initialization

```bash
# Apply migrations to create schema
uv run alembic upgrade head

# Verify database connection
uv run python -c "from src.core.db import AsyncDatabase; print('✓ Database connected')"
```

## Usage

### REST API (Recommended for Production)

#### Starting the Server

```bash
# Development mode with auto-reload
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

#### Authentication Flow

```bash
# 1. Create user account
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "nickname": "John",
    "password": "SecurePassword123!"
  }'

# 2. Obtain JWT token
curl -X POST http://localhost:8000/api/v1/security/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=john_doe&password=SecurePassword123!'

# Response: {"access_token": "eyJ0eXAi...", "token_type": "bearer"}

# 3. Use token in subsequent requests
TOKEN="eyJ0eXAi..."
curl -X GET http://localhost:8000/api/v1/habits \
  -H "Authorization: Bearer $TOKEN"
```

### API Documentation

#### Habit Management

**Create Habit**
```http
POST /api/v1/habits
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Morning Meditation",
  "description": "Daily 10-minute meditation session",
  "frequency": "daily",
  "tags": "wellness,mindfulness"
}
```

**List All Habits**
```http
GET /api/v1/habits
Authorization: Bearer {token}
```

**Mark Habit as Complete**
```http
POST /api/v1/habits/{habit_id}/complete
Authorization: Bearer {token}
```

**Update Habit**
```http
PUT /api/v1/habits/{habit_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "description": "Updated description",
  "frequency": "weekly"
}
```

**Delete Habit**
```http
DELETE /api/v1/habits/{habit_id}
Authorization: Bearer {token}
```

**Get At-Risk Habits**
```http
GET /api/v1/habits/at-risk?days=3
Authorization: Bearer {token}
```
Returns habits not completed for specified number of days.

**Get AI Coaching**
```http
GET /api/v1/habits/at-risk/ai-coach?user_id={user_id}
Authorization: Bearer {token}
```
Returns at-risk habits with AI-generated personalized coaching advice.

#### User Management

**Get Current User Profile**
```http
GET /api/v1/users/me
Authorization: Bearer {token}
```

**Update User Profile**
```http
PUT /api/v1/users/{user_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "nickname": "New Nickname",
  "role": "user"
}
```

**Delete User Account**
```http
DELETE /api/v1/users/me
Authorization: Bearer {token}
```

#### Reports & Analytics

**Generate Weekly Report**
```http
POST /api/v1/reports
Authorization: Bearer {token}
```
Triggers asynchronous weekly report generation via AWS SQS.

**Download Report (PDF)**
```http
GET /api/v1/reports/{report_id}
Authorization: Bearer {token}
```

### Command-Line Interface

#### Interactive Mode (Recommended for Beginners)

```bash
uv run python -m src.cli.main interactive
```

Interactive prompts guide you through:
- User authentication or creation
- Habit management (add, list, complete)
- Navigation with friendly menus

#### Direct Command Mode

```bash
# Add a new habit
uv run python -m src.cli.main add \
  --name "Exercise" \
  --description "30-minute workout routine" \
  --frequency daily

# Mark habit as complete
uv run python -m src.cli.main complete --habit-id {habit_id}

# List all habits for user
uv run python -m src.cli.main list

# View weekly statistics
uv run python -m src.cli.main stats --week-number 1

# Generate PDF report
uv run python -m src.cli.main report --output ./report.pdf

# View help
uv run python -m src.cli.main --help
```

## Project Structure

```
habit-tracker/
├── alembic/                        # Database migration management
│   ├── versions/                  # Individual migration scripts
│   ├── env.py                     # Alembic environment configuration
│   └── script.py.mako             # Migration template
│
├── src/
│   ├── api/                        # FastAPI REST API (Presentation Layer)
│   │   ├── main.py               # Application entry point, middleware, startup/shutdown
│   │   ├── exception_handlers.py  # Custom exception handlers
│   │   └── v1/                   # API version 1 routes
│   │       └── routers/
│   │           ├── admin.py      # Administrative endpoints
│   │           ├── dependencies.py # Dependency injection setup
│   │           ├── habits.py     # Habit CRUD and AI coaching endpoints
│   │           ├── reports.py    # Report generation endpoints
│   │           ├── security.py   # Authentication endpoints
│   │           └── users.py      # User management endpoints
│   │
│   ├── core/                       # Business Logic Layer
│   │   ├── cache.py              # Redis cache management
│   │   ├── db.py                 # Database session management
│   │   ├── events/               # Event-driven architecture
│   │   │   ├── dispatcher.py    # Event dispatching mechanism
│   │   │   ├── events.py        # Event definitions
│   │   │   └── handlers.py      # Event subscription and handling
│   │   ├── exceptions.py         # Custom domain exceptions
│   │   ├── habit.py              # Synchronous habit operations (legacy)
│   │   ├── habit_async.py        # Asynchronous habit & user services
│   │   ├── models.py             # SQLAlchemy ORM model definitions
│   │   ├── schemas.py            # Pydantic request/response schemas
│   │   └── security.py           # Authentication, JWT, password hashing
│   │
│   ├── infrastructure/             # Infrastructure Layer
│   │   ├── ai/                    # AI/ML integrations
│   │   │   └── ollama_client.py # Ollama LLM client for habit coaching
│   │   ├── aws/                   # AWS service integrations
│   │   │   ├── aws_helper.py    # AWS session and stack management
│   │   │   ├── email_client.py  # AWS SES email delivery
│   │   │   ├── queue_client.py  # AWS SQS job queue management
│   │   │   ├── s3_client.py     # AWS S3 file storage
│   │   │   └── worker.py        # Background job processing
│   │   └── pdf/                   # Report generation
│   │       ├── report_pdf.py    # PDF document generation
│   │       └── reports_service.py # Report data aggregation
│   │
│   ├── repository/                 # Data Access Layer
│   │   ├── base.py               # Base repository interface
│   │   ├── habit_repository.py   # Habit data access operations
│   │   └── user_repository.py    # User data access operations
│   │
│   └── utils/                      # Utilities & Helpers
│       ├── decorators.py         # Caching and timing decorators
│       ├── helpers.py            # General utility functions
│       └── logger.py             # Centralized logging configuration
│
├── tests/                          # Test Suite (3+ test types)
│   ├── conftest.py               # Shared pytest fixtures & factories
│   ├── test_cache_redis.py       # Redis caching integration tests
│   ├── test_config.py            # Configuration tests
│   ├── test_habit_api.py         # API endpoint integration tests
│   ├── test_habit_history.py     # Habit history model tests
│   ├── test_habit_manager.py     # Habit manager service unit tests
│   ├── test_habit_repository.py  # Repository layer integration tests
│   ├── test_habit_update.py      # Habit update schema tests
│   ├── test_handlers.py          # Event handler unit tests
│   ├── test_handlers_extended.py # Extended event handler tests
│   ├── test_ollama_client.py     # AI coaching integration tests
│   ├── test_reports.py           # Report generation tests
│   ├── test_s3_client.py         # S3 integration tests
│   ├── test_user_manager.py      # User manager service tests
│   ├── test_user_repository.py   # User repository tests
│   ├── test_user_service.py      # User service unit tests
│   ├── test_worker.py            # Background worker tests
│   └── test_habit_api.py         # Comprehensive API tests
│
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore rules
├── alembic.ini                    # Alembic configuration
├── conftest.py                    # Pytest configuration & global fixtures
├── docker-compose.yaml            # Multi-container orchestration
├── Dockerfile                     # Application container definition
├── justfile                       # Just command shortcuts
├── pyproject.toml                 # Project metadata and dependencies
├── README.md                      # This file
└── requirements.txt              # Python dependencies (optional)
```

### Layer Responsibilities

| Layer | Responsibility | Technologies |
|-------|----------------|--------------|
| **Presentation** | HTTP handling, request validation, response formatting | FastAPI, Pydantic |
| **Business Logic** | Use cases, workflows, domain rules, event handling | Python, AsyncIO |
| **Data Access** | Database queries, caching, persistence | SQLAlchemy, Redis |
| **Infrastructure** | External services, file I/O, cloud APIs | AWS, Ollama, Email |

## Development

### Local Development Setup

#### 1. Install Development Dependencies

```bash
# Use uv for faster dependency resolution
uv sync

# Or use pip with requirements file
pip install -r requirements-dev.txt
```

#### 2. Configure Pre-commit Hooks (Optional)

```bash
# Install pre-commit framework
pip install pre-commit

# Configure git hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

### Testing Strategy

The project implements comprehensive test coverage across three dimensions:

#### Unit Tests
Tests for isolated components (services, repositories, utilities) without external dependencies.

```bash
# Run unit tests only
uv run pytest -m unit -v

# Run with coverage
uv run pytest -m unit --cov=src --cov-report=html
```

#### Integration Tests
Tests for layer interactions (API endpoints, database operations, cache operations).

```bash
# Run integration tests (requires Docker or running services)
uv run pytest -m integration -v
```

#### End-to-End Tests
Full workflow tests simulating real user scenarios.

```bash
# Run E2E tests
uv run pytest -m e2e -v
```

#### Running All Tests

```bash
# All tests with coverage report
uv run pytest --cov=src --cov-report=html --cov-report=term-missing

# Specific test file
uv run pytest tests/test_habit_api.py -v

# Specific test function
uv run pytest tests/test_habit_api.py::test_create_habit_positive -vvs

# With live output and print statements
uv run pytest -s -v

# Run tests in parallel (faster)
uv run pytest -n auto

# Run tests and track coverage
just test-cov
```

#### Test Organization

- **Fixtures**: Defined in `conftest.py` with scope management (function, session)
- **Mocking**: AsyncMock for async components, MagicMock for sync components
- **Factories**: Data generation for test scenarios (FakeUserFactory, FakeHabitFactory)
- **Containers**: Testcontainers for isolated PostgreSQL and Redis instances

### Code Quality Tools

#### Linting & Formatting

```bash
# Format code with Ruff (auto-fix)
uv run ruff format .

# Check formatting without changes
uv run ruff format . --check

# Lint code (find issues)
uv run ruff check . --fix

# Use justfile shortcuts
just fmt
just lint
```

#### Type Checking

```bash
# Run mypy type checker
uv run mypy .

# Run with strict mode
uv run mypy . --strict

# Check specific file
uv run mypy src/core/habit_async.py

# Use justfile shortcut
just typecheck
```

#### Code Coverage

```bash
# Generate coverage report
uv run pytest --cov=src --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Database Management

#### Migrations with Alembic

```bash
# Create new migration (auto-generates based on model changes)
uv run alembic revision --autogenerate -m "descriptive message"

# Review generated migration
nano alembic/versions/xxx_descriptive_message.py

# Apply pending migrations
uv run alembic upgrade head

# Check migration status
uv run alembic current

# Rollback one version
uv run alembic downgrade -1

# Rollback to specific revision
uv run alembic downgrade abc123

# Create empty migration (for custom SQL)
uv run alembic revision -m "custom changes"
```

#### Database Shell Access

```bash
# PostgreSQL interactive shell
psql postgresql://user:password@localhost:5432/habit_tracker

# Useful SQL commands
SELECT * FROM users;
SELECT COUNT(*) FROM habits;
SELECT * FROM habit_completions ORDER BY completed_at DESC;
```

### Docker Development

#### Building Images

```bash
# Build application image
docker build -t habit-tracker:latest .

# Build with build arguments
docker build \
  --build-arg PYTHON_VERSION=3.13 \
  -t habit-tracker:latest .
```

#### Running Containers

```bash
# Run single service
docker run -p 8000:8000 habit-tracker:latest

# Run with environment file
docker run --env-file .env -p 8000:8000 habit-tracker:latest

# Interactive shell in container
docker exec -it habit-tracker bash
```

#### Docker Compose Workflow

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api
docker-compose logs -f postgres
docker-compose logs -f redis

# Stop all services
docker-compose down

# Remove volumes (reset data)
docker-compose down -v

# Rebuild images
docker-compose build --no-cache
```

### Development Workflows

#### Running the Application

```bash
# Start API server with hot reload
uv run uvicorn src.api.main:app --reload --host 0.0.0.0

# Start with specific log level
uv run uvicorn src.api.main:app --reload --log-level debug

# Start CLI in interactive mode
uv run python -m src.cli.main interactive
```

#### Debugging

```bash
# Enable SQL query logging
export DATABASE_ECHO=true
uv run uvicorn src.api.main:app --reload

# Enable debug logging
export LOG_LEVEL=DEBUG
uv run uvicorn src.api.main:app --reload

# Use Python debugger
# Add this to code: import pdb; pdb.set_trace()
```

#### Using Just Commands

View available commands:
```bash
just --list
```

Common commands:
```bash
just install      # Install dependencies
just fmt         # Format code
just lint        # Lint code
just typecheck   # Run type checker
just test        # Run tests
just test-cov    # Run tests with coverage
just serve       # Start development server
```

## Performance & Scalability

### Caching Strategy

The application implements multi-layer caching for optimal performance:

#### Redis Caching
```python
# Automatic caching for frequently accessed data
from src.infrastructure.cache import get_cache_client

cache = get_cache_client()
cached_habits = await cache.get("user:123:habits")
if not cached_habits:
    habits = await habit_service.get_habits(user_id=123)
    await cache.set("user:123:habits", habits, ttl=3600)
```

#### Cache Invalidation
```python
# Invalidate when data changes
await cache.delete("user:123:habits")
await cache.delete_prefix("user:123:*")  # Invalidate all user data
```

### Async/Await Pattern

All I/O-bound operations use `async/await` for non-blocking concurrency:

```python
# Correct - concurrent requests
responses = await asyncio.gather(
    session.get(url1),
    session.get(url2),
    session.get(url3),
    return_exceptions=True
)

# Avoid - sequential (blocking)
r1 = await session.get(url1)
r2 = await session.get(url2)  # Wait for r1 before starting
```

### Database Optimization

#### Connection Pooling
- SQLAlchemy manages Psycopg2 connection pool (default: 5-20 connections)
- Configure via environment variable:
```bash
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
```

#### Query Optimization
- Lazy loading disabled (eager loading recommended)
- Pagination for list endpoints:
```python
@router.get("/habits")
async def list_habits(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    return await habit_service.list_habits(skip=skip, limit=limit)
```

#### Indexes
Primary indexes configured on:
- `users.id` (primary key)
- `habits.user_id` (foreign key)
- `habit_completions.habit_id` (queries)
- `habit_completions.completed_at` (time-based queries)

### Load Testing

```bash
# Install load testing tool
pip install locust

# Create locustfile.py with test scenarios
# Run load tests
locust -f locustfile.py --host=http://localhost:8000
```

### Horizontal Scaling

#### Cloud Deployment (AWS)

**ECS Fargate for containerized scaling:**
```python
# Application stateless - can run multiple instances
# Database connection pool managed per instance
# Redis for shared state across instances
```

**Infrastructure as Code (CloudFormation):**
```bash
# Deploy stack
aws cloudformation create-stack \
  --stack-name habit-tracker-prod \
  --template-body file://cloudformation.yaml

# Update stack
aws cloudformation update-stack \
  --stack-name habit-tracker-prod \
  --template-body file://cloudformation.yaml
```

#### Message Queue (SQS)

For asynchronous task processing:
```python
from src.infrastructure.aws.queue_client import QueueClient

queue = QueueClient()

# Send message for async processing
await queue.send_message(
    queue_url="https://sqs.region.amazonaws.com/queue-name",
    message_body={"habit_id": 123, "action": "analyze"}
)

# Process messages in worker
async for message in queue.receive_messages(queue_url):
    await process_habit_analysis(message)
    await queue.delete_message(queue_url, message['ReceiptHandle'])
```

#### Email Service (SES)

Send notifications asynchronously:
```python
from src.infrastructure.aws.email_client import EmailClient

email = EmailClient()

await email.send_email(
    to_addresses=["user@example.com"],
    subject="Habit Reminder",
    body="Time to complete your morning workout!",
    html_body="<p>Time to complete your morning workout!</p>"
)
```

## Security

### Authentication & Authorization

#### JWT Token Management
```python
# Tokens issued with configurable TTL
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Token stored in HTTP-only cookies (CSRF protection)
# Automatic refresh on token expiration
```

#### Password Security
```python
# Uses bcrypt via pwdlib
# Minimum requirements enforced:
# - 8+ characters
# - Mix of uppercase, lowercase, numbers, symbols
# - Not in top 100 common passwords

from src.core.security import verify_password, hash_password

hashed = hash_password("user_password_123")
is_valid = verify_password("user_password_123", hashed)
```

### Data Protection

#### In Transit
- TLS/HTTPS enforced for all production connections
- CORS policy restricts cross-origin requests
- CSRF tokens validated on state-changing operations

#### At Rest
- Database encrypted at AWS RDS level
- Secret keys stored in AWS Secrets Manager (not in code)
- Environment variables for configuration (no hardcoded secrets)

#### Compliance
- GDPR: User data export and deletion implemented
- User data isolated by user_id (no cross-user access)
- Audit logs track sensitive operations

### API Security

#### Rate Limiting (Planned)
```python
# SlowAPI integration ready for rate limiting
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@router.get("/habits", dependencies=[Depends(limiter.limit("100/minute"))])
async def list_habits():
    pass
```

#### Input Validation
- Pydantic v2 for strict schema validation
- Type hints enforced with mypy
- SQL injection prevention via ORM parameterized queries

#### Output Sanitization
- Sensitive fields excluded from responses (password hashes, tokens)
- Proper HTTP status codes for all scenarios
- Error messages don't leak system details

### Environment Variables

Never commit secrets. Use `.env` file (gitignored):

```bash
# Security
SECRET_KEY=your-256-bit-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/habit_tracker

# AWS Services
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# Ollama
OLLAMA_BASE_URL=http://localhost:11434

# Email
ADMIN_EMAIL=admin@example.com
```

### AWS IAM Permissions

Minimal permissions principle:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::habit-tracker-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage"
      ],
      "Resource": "arn:aws:sqs:*:*:habit-tracker-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:DescribeStacks"
      ],
      "Resource": "*"
    }
  ]
}
```

## Troubleshooting

### Common Issues

#### 1. "model 'llama-3.1:latest' not found"

**Symptom**: Ollama integration fails with model not found error

**Root Cause**: Model name mismatch (dash vs dot separator)

**Solution**:
```bash
# Check available models
ollama list

# Correct model name (dot, not dash)
OLLAMA_MODEL=llama3.1:latest

# Verify Ollama service is running
curl http://localhost:11434/api/tags
```

#### 2. Ollama Request Timeout

**Symptom**: First request to Ollama takes 30+ seconds

**Root Cause**: Model loading on first request, or network latency

**Solution**:
```bash
# Increase timeout for slow systems
OLLAMA_TIMEOUT=120  # seconds

# Pre-load model
ollama pull llama3.1:latest

# Verify response time
curl -w "Total time: %{time_total}\n" http://localhost:11434/api/generate
```

#### 3. PostgreSQL Connection Error

**Symptom**: `psycopg2.OperationalError: connection to server failed`

**Root Cause**: Database service not running or incorrect credentials

**Solution**:
```bash
# Start database with Docker
docker-compose up -d postgres

# Verify connection
psql $DATABASE_URL -c "SELECT 1"

# Check credentials in .env
cat .env | grep DATABASE_URL
```

#### 4. Alembic Migration Offline

**Symptom**: `Cannot access database to autogenerate migration`

**Root Cause**: Alembic autogenerate needs live database connection

**Solution**:
```bash
# Option 1: Start database first
docker-compose up -d postgres
uv run alembic upgrade head

# Option 2: Create empty migration for manual edits
uv run alembic revision -m "description"

# Option 3: Disable autogenerate in alembic.ini
sqlalchemy.url = driver://user:pass@localhost/dbname
```

#### 5. MyPy Type Checking Failures

**Symptom**: `error: No library stub...` or `Unsupported operand type...`

**Root Cause**: Missing type stubs or incorrect type hints

**Solution**:
```bash
# Run mypy with verbose output
uv run mypy . --show-error-codes --show-error-context

# Install missing stubs
uv pip install types-requests types-PyYAML

# Suppress specific errors (if acceptable)
# In file: a = some_function()  # type: ignore[no-any-return]

# Check specific file
uv run mypy src/api/main.py --strict
```

#### 6. Redis Connection Failed

**Symptom**: `ConnectionError: Error 111 connecting to localhost:6379`

**Root Cause**: Redis service not running

**Solution**:
```bash
# Start Redis with Docker
docker-compose up -d redis

# Verify connection
redis-cli ping

# Check Redis health
redis-cli info
```

#### 7. Test Database Lock

**Symptom**: `psycopg2.OperationalError: another session using the database`

**Root Cause**: Previous test session still holding connection

**Solution**:
```bash
# Drop test database
dropdb habit_tracker_test

# Or force close connections
psql -U postgres -d template1 << EOF
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'habit_tracker_test';
DROP DATABASE IF EXISTS habit_tracker_test;
EOF

# Re-run tests
uv run pytest
```

#### 8. Docker Container Exits Immediately

**Symptom**: Container starts then stops with exit code 1

**Root Cause**: Application error or missing environment variables

**Solution**:
```bash
# Check logs
docker-compose logs api

# Verify environment (.env exists and is readable)
ls -la .env

# Run container interactively
docker-compose run --rm api /bin/bash

# Test application startup
docker-compose up api --no-detach
```

### Performance Issues

#### Slow Query Execution

```bash
# Enable SQL logging
export DATABASE_ECHO=true
uv run uvicorn src.api.main:app --reload

# Or use connection.echo = True in SQLAlchemy
```

#### High Memory Usage

```bash
# Check cache configuration
redis-cli info memory

# Reduce cache TTL
await cache.set("key", value, ttl=300)  # 5 minutes instead of 1 hour

# Monitor with top
docker stats
```

#### CPU Bottlenecks

```bash
# Profile with cProfile
python -m cProfile -s cumulative src/api/main.py

# Use async profilers
pip install py-spy
py-spy record -o profile.svg -- uvicorn src.api.main:app
```

### Debug Mode

Enable comprehensive logging:

```bash
# Set environment variables
export LOG_LEVEL=DEBUG
export DATABASE_ECHO=true
export PYTHONUNBUFFERED=true

# Start application
uv run uvicorn src.api.main:app --reload --log-level debug

# View all logs
docker-compose logs -f
```

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
