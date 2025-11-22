ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS base

RUN apt-get update && apt-get install -y \
    libpq-dev build-essential curl \
    && rm -rf /var/lib/apt/lists/*

RUN adduser --uid 5555 --disabled-password app
WORKDIR /workspace

# Build
FROM base AS build
RUN pip install --no-cache-dir uv
ENV UV_PROJECT_ENVIRONMENT=/workspace/api/.venv

# Copy the entire backend structure to maintain relative paths
COPY shared /workspace/shared/
COPY api /workspace/api/

# Install shared module first
RUN cd /workspace/shared && pip install .

# Install planner dependencies with uv
WORKDIR /workspace/api
RUN uv sync --frozen

# Local dev
FROM build AS localdev
ENV PYTHONUNBUFFERED=1 ENV=local
ENV PATH=/workspace/api/.venv/bin:$PATH
WORKDIR /workspace/api

CMD ["hypercorn", "src.main:app", "--bind", "0.0.0.0:8080", "--reload"]

# Production
FROM base AS dist
COPY --chown=app:app --from=build /workspace/api /workspace/api
COPY --chown=app:app --from=build /workspace/shared /workspace/shared
RUN pip install --no-cache-dir uv && cd /workspace/shared && pip install .
USER 5555

ENV PATH=/workspace/api/.venv/bin:$PATH
ENV PYTHONUNBUFFERED=1 HYPERCORN_WORKERS=1
WORKDIR /workspace/api

CMD ["sh", "-c", "hypercorn src.main:app --bind 0.0.0.0:8080 --workers ${HYPERCORN_WORKERS}"]
