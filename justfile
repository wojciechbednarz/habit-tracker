# justfile
set dotenv-load

# List all available commands
default:
    @just --list

# Install dependencies
install:
    uv sync

# Format code
fmt:
    uv run ruff format .

# Lint code
lint:
    uv run ruff check --fix .

# Type check
typecheck:
    uv run mypy src/

# Run tests
test:
    uv run pytest

# Run tests with coverage
test-cov:
    uv run pytest --cov=habit-tracker --cov-report=html --cov-report=term

# Run all checks (lint, typecheck, test)
check: lint typecheck test

# Clean up cache and build artifacts
clean:
    rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
    find . -type d -name __pycache__ -exec rm -rf {} +

# Install pre-commit hooks
hooks:
    uv run pre-commit install

# Run pre-commit on all files
pre-commit-all:
    uv run pre-commit run --all-files

# Run the habit tracker
run:
    uv run python -m src.core.habit
