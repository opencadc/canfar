# syntax=docker/dockerfile:1

# renovate: datasource=docker depName=ghcr.io/astral-sh/uv versioning=semver
FROM ghcr.io/astral-sh/uv:alpine@sha256:2164449704885d86f8fc445c3b02e2e67d317f3f623ba504a87561be7496767b AS uv

# renovate: datasource=docker depName=python versioning=python
FROM python:alpine@sha256:9e9fde4d32eedce0b661d9ab91e826b62dddf28e928c230ec55f1866cac66b01 AS builder

WORKDIR /build

COPY --from=uv /usr/local/bin/uv /usr/local/bin/uv
COPY --from=uv /usr/local/bin/uvx /usr/local/bin/uvx

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY canfar/ ./canfar/

RUN uv build --wheel --out-dir /dist \
    && uv pip install --prefix=/install /dist/*.whl

# renovate: datasource=docker depName=python versioning=python
FROM python:alpine@sha256:9e9fde4d32eedce0b661d9ab91e826b62dddf28e928c230ec55f1866cac66b01 AS production

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
