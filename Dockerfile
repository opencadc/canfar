# syntax=docker/dockerfile:1

# renovate: datasource=docker depName=ghcr.io/astral-sh/uv versioning=semver
FROM ghcr.io/astral-sh/uv:alpine@sha256:a788290ce829958f18bcea1dfd9fb5dcf4bfb22f6380b52c9322f9d91e86b117 AS uv

# renovate: datasource=docker depName=python versioning=python
FROM python:alpine@sha256:a0f2e268f2ce8f3709611a90054ec6a8ae31f6251f5896b8648b9bb99835e30a AS builder

WORKDIR /build

COPY --from=uv /usr/local/bin/uv /usr/local/bin/uv
COPY --from=uv /usr/local/bin/uvx /usr/local/bin/uvx

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY canfar/ ./canfar/

RUN uv build --wheel --out-dir /dist \
    && uv pip install --prefix=/install /dist/*.whl

# renovate: datasource=docker depName=python versioning=python
FROM python:alpine@sha256:a0f2e268f2ce8f3709611a90054ec6a8ae31f6251f5896b8648b9bb99835e30a AS production

LABEL org.opencontainers.image.title="CANFAR Python CLI" \
      org.opencontainers.image.description="CLI for CANFAR Science Platform" \
      org.opencontainers.image.vendor="Canadian Astronomy Data Centre" \
      org.opencontainers.image.source="https://github.com/opencadc/canfar" \
      org.opencontainers.image.licenses="AGPL-3.0-or-later"

COPY --from=builder /install /usr/local

HEALTHCHECK --interval=1s --timeout=15s --retries=3 --start-period=1s \
    CMD ["canfar", "--help"]

ENTRYPOINT ["canfar"]
CMD ["--help"]
