FROM python:3.13-alpine@sha256:18159b2be11db91f84b8f8f655cd860f805dbd9e49a583ddaac8ab39bf4fe1a7 AS base

FROM base AS builder
COPY . /canfar
WORKDIR /canfar

# Install UV
RUN set -ex \
    && apk add --no-cache curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && source $HOME/.local/bin/env \
    && uv build

FROM base AS production
COPY --from=builder /canfar/dist /canfar/dist
RUN pip install --no-cache-dir /canfar/dist/*.whl
CMD ["/bin/sh", "-c", "canfar"]
