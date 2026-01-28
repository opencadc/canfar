# syntax=docker/dockerfile:1

# renovate: datasource=docker depName=ghcr.io/astral-sh/uv versioning=semver
FROM ghcr.io/astral-sh/uv:alpine AS uv

# renovate: datasource=docker depName=python versioning=python
FROM python:alpine AS builder

WORKDIR /build

COPY --from=uv /usr/local/bin/uv /usr/local/bin/uv
COPY --from=uv /usr/local/bin/uvx /usr/local/bin/uvx

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY canfar/ ./canfar/

RUN uv build --wheel --out-dir /dist \
    && uv pip install --prefix=/install /dist/*.whl

# renovate: datasource=docker depName=python versioning=python
FROM python:alpine AS runtime

LABEL org.opencontainers.image.title="CANFAR Python CLI" \
      org.opencontainers.image.description="CLI for CANFAR Science Platform" \
      org.opencontainers.image.vendor="Canadian Astronomy Data Centre" \
      org.opencontainers.image.source="https://github.com/opencadc/canfar" \
      org.opencontainers.image.licenses="AGPL-3.0-or-later"

COPY --from=builder /install /usr/local

CMD ["canfar"]
