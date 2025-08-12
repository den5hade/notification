FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the project into the image
ADD . /app

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app

RUN uv sync --locked

# Expose any necessary ports (e.g., for a web application)
EXPOSE 8030

# Define the command to run your application
CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8030"]