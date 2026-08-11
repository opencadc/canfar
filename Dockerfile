# syntax=docker/dockerfile:1

# renovate: datasource=docker depName=ghcr.io/astral-sh/uv versioning=semver
FROM ghcr.io/astral-sh/uv:alpine@sha256:5c122244bea9d255105d4d4400de450ec171296733a326eba624e0278cf0c75e AS uv

# renovate: datasource=docker depName=python versioning=python
FROM python:alpine@sha256:a1321512d6a287428c50dcdf2ab3857761127e03a23b1f648e9c1c0de59288f8 AS builder

WORKDIR /build

COPY --from=uv /usr/local/bin/uv /usr/local/bin/uv
COPY --from=uv /usr/local/bin/uvx /usr/local/bin/uvx

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY canfar/ ./canfar/

RUN uv build --wheel --out-dir /dist \
    && uv pip install --prefix=/install /dist/*.whl

# renovate: datasource=docker depName=python versioning=python
FROM python:alpine@sha256:a1321512d6a287428c50dcdf2ab3857761127e03a23b1f648e9c1c0de59288f8 AS production

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
