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
    ruff format .

# Lint code
lint:
    ruff check .

# Type check
typecheck:
    mypy src/

# Run tests
test:
    pytest

# Run tests with coverage
test-cov:
    pytest --cov=habit_tracker --cov-report=html --cov-report=term

# Run all checks (lint, typecheck, test)
check: lint typecheck test

# Clean up cache and build artifacts
clean:
    rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
    find . -type d -name __pycache__ -exec rm -rf {} +

# Install pre-commit hooks
hooks:
    pre-commit install

# Run pre-commit on all files
pre-commit-all:
    pre-commit run --all-files