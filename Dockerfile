FROM ghcr.io/astral-sh/uv:0.9.11-python3.12-bookworm-slim

ARG UID=1000
ARG GID=1000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update \
    && apt-get install --no-install-recommends -y tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid "${GID}" app \
    && useradd --uid "${UID}" --gid "${GID}" --create-home app

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/
RUN uv sync --locked --no-dev --no-editable --no-cache \
    && mkdir -p /app/secrets /app/data \
    && chown app:app /app/secrets /app/data

USER app

ENTRYPOINT ["email-classificator"]
CMD ["classify"]
