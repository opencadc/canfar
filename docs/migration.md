# Migration Guide: skaha → canfar

In summer 2025, this source code was migrated from [shinybrar/skaha](https://github.com/shinybrar/skaha) to [opencadc/canfar](https://github.com/opencadc/canfar) to be officially supported by the Canadian Astronomy Data Centre (CADC). Along with this move, the package was migrated from `skaha` to `canfar` better reflect a unified naming scheme accross the Science Platform.

This guide helps you migrate from the `skaha` python package to `canfar`.

## Summary of Changes

- Package rename: `skaha` → `canfar`.
- Public API: import session via `from canfar.session import AsyncSession` (and `Session`).
- Client Rename: `SkahaClient` → `HTTPClient`
- Config Path: `~/.skaha/config.yaml` → `~/.canfar/config.yaml`.
- Logger: `canfar`; logs under `~/.canfar/client.log`.
- ENV vars: `SKAHA_…` → `CANFAR_…`
- CLI: `canfar` is the only entrypoint
- User-Agent: `python-canfar/{version}`.
- Protocol contracts: Server URLs and custom headers remain unchanged (e.g., `https://ws-uv.canfar.net/skaha`, `X-Skaha-Authentication-Type`, `X-Skaha-Registry-Auth`).

## Code Examples

- Python client session:
  - Before: `from skaha.session import AsyncSession`
  - After: `from canfar.session import AsyncSession`

- Client composition:
  - Before: `from skaha.client import SkahaClient`
  - After: `from canfar.client import HTTPClient`

## Environment variables

- Before: `SKAHA_TIMEOUT`, `SKAHA_CONCURRENCY`, `SKAHA_TOKEN`, `SKAHA_URL`, `SKAHA_LOGLEVEL`…
- After: `CANFAR_TIMEOUT`, `CANFAR_CONCURRENCY`, `CANFAR_TOKEN`, `CANFAR_URL`, `CANFAR_LOGLEVEL`…

## Configuration

- Default config file moves from `~/.skaha/config.yaml` to `~/.canfar/config.yaml`.
- The structure of the YAML file remains the same.

## Docs and Links:

- Repo: `https://github.com/opencadc/canfar`
- Docs: `https://opencadc.github.io/canfar/`
- Changelog: `https://opencadc.github.io/canfar/changelog/`

## Notes on protocol stability:

- Server base path segments under `/skaha` are server-side contracts and are unchanged.
- Historical header names are unchanged and documented above.

