#################
## Build stage ##
#################
FROM python:3.14-alpine AS build

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy required project files
COPY src/ /app/src/
COPY pyproject.toml uv.lock README.md /app/

WORKDIR /app
RUN uv sync --frozen --no-dev


#################
## Final stage ##
#################
FROM python:3.14-alpine

# Copy the app from build stage
COPY --from=build /app /app

# Copy config file
COPY config.yaml /app/

WORKDIR /app

EXPOSE 8000

CMD ["/app/.venv/bin/uvicorn", "llmock.app:app", "--host", "0.0.0.0", "--port", "8000"]
