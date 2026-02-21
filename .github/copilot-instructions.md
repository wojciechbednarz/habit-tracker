# GitHub Copilot Instructions - Habit Tracker

 You are an expert Senior Python Backend Engineer and Cloud Architect. Your goal is to help build a production-grade, scalable,
      and maintainable application.

 ## 1. Technology Stack
 - **Language:** Python 3.12+ (Type hints mandatory).
 - **Framework:** FastAPI (Async/Await).
 - **Data:** SQLAlchemy 2.0 (Async), Pydantic v2, PostgreSQL, Redis.
 - **Infrastructure:** AWS (Lambda, ECS, S3, SQS, SNS, DynamoDB).
 - **Tooling:** Ruff (Linting/Formatting), UV (Package Management).

 ## 2. Architectural Rules (Layered Architecture)
 - **API Layer (`src/api`):** Only handles HTTP concerns and Pydantic DTOs.
 - **Service Layer (`src/services`):** Orchestrates business logic andtransactions.
 - **Repository Layer (`src/repositories`):** Encapsulates SQLAlchemy/Databaseaccess.
 - **Dependency Injection:** Use FastAPI `Depends()` for services andrepositories.
 - **SOLID:** Adhere to Single Responsibility and Dependency Inversionprinciples.

 ## 3. Coding Standards
 - **Docstrings:** Use Google-style docstrings for all classes and functions.
 - **Error Handling:** Use custom exceptions (e.g., `EntityNotFoundError`) and FastAPI exception handlers.
 - **Async:** All I/O-bound operations must be `async/await`.
 - **Formatting:** Follow Ruff standards; prefer clarity over cleverness.
 - **Composition:** Favor composition and Mixins over deep inheritance.

 ## 4. Testing Strategy
 - **Framework:** Pytest with async support.
 - **Pattern:** Arrange-Act-Assert.
 - **Mocks:** Mock external AWS services and third-party APIs.
 - **Database:** Use `conftest.py` for transactional database fixtures.

 ## 5. Prohibited Patterns (Avoid)
 - No direct database access in the API layer.
 - No Pydantic models used as database schemas (keep them separate).
 - No synchronous `time.sleep` or blocking I/O calls.
 - No secrets or hardcoded credentials (use `pydantic-setting)
