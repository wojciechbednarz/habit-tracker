"""Lambda entry. Mangum wraps FastAPI app for API Gateway proxy events.

DB auth via RDS IAM tokens (no passwords). Token regenerated each cold start
(15-min validity). SQLAlchemy pool_recycle must stay below 900s.
"""

import os

if not os.getenv("DATABASE_URL") and os.getenv("DB_HOST"):
    os.environ["DATABASE_URL"] = (
        f"postgresql+asyncpg://{os.environ['DB_USER']}"
        f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
    )


from mangum import Mangum  # noqa: E402

from src.api.main import app  # noqa: E402

lambda_handler = Mangum(app=app, lifespan="off")
