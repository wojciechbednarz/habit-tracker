FROM python:3.12-slim-trixie

WORKDIR /app

# Copy from the cache instead of linking
ENV UV_LINK_MODE=copy

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    git \
 && rm -rf /var/lib/apt/lists/*

# Copy uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the rest of the application
COPY . /app

# Install dependencies
RUN uv sync --frozen

CMD ["uv", "run", "fastapi", "dev", "src/api/main.py", "--port", "8000", "--reload", "--host", "0.0.0.0"]
