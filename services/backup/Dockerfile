FROM alpine:latest

# Install system dependencies: python3, rclone, docker-cli, and tools for uv
RUN apk add --no-cache \
    python3 \
    rclone \
    curl \
    ca-certificates \
    docker-cli \
    docker-cli-compose

# Install uv from the official binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory to /app where the project will be mounted
WORKDIR /app

# The user inside the container must be root
USER root

# Entrypoint is tools.py
# We use 'uv run' to ensure dependencies from pyproject.toml are available
ENTRYPOINT ["uv", "run", "tools.py"]
