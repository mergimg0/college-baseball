FROM python:3.13-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install git (needed for the push step)
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Copy project files and install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY fsbb/ fsbb/
COPY scripts/ scripts/
COPY migrations/ migrations/
COPY data/pear/ data/pear/

# Mount DB at runtime: -v ./data/fsbb.db:/app/data/fsbb.db
# Mount docs for output: -v ./docs:/app/docs
RUN mkdir -p data logs docs

ENTRYPOINT ["bash"]
CMD ["scripts/daily_update.sh"]
