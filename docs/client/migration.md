# skaha → canfar

In summer 2025, the CANFAR Python client was moved from [shinybrar/skaha](https://github.com/shinybrar/skaha) to [opencadc/canfar](https://github.com/opencadc/canfar) to be officially supported by the Canadian Astronomy Data Centre (CADC). As part of this move, the Python package was renamed from `skaha` to `canfar` to better reflect a unified naming scheme across the CANFAR Science Platform.

This guide helps you migrate from the `skaha` Python package to `canfar`.

## Summary of changes

- Package name: `skaha` → `canfar`.
- **Breaking Changes**
  - `skaha.session` → `canfar.sessions`.
  - `headless` session `kind` parameter is no longer required.
  - `session.info()` query now returns `Completed` instead of `Succeeded`.
- Configuration path: `~/.skaha/config.yaml` → `~/.canfar/config.yaml`.
- Logger name and location: logger `canfar`; logs under `~/.canfar/client.log`.
- Environment variables: prefix change `SKAHA_…` → `CANFAR_…`.
- CLI entry point: `canfar` (single entry point).
- User-Agent header: `python-canfar/{version}`.
- Protocol contracts: server URLs and custom headers remain unchanged (see notes below).

## Code Examples

- Python client session

    ```python title="Before"
    from skaha.session import AsyncSession, Session
    ```
    
    ```python title="After"
    from canfar.sessions import AsyncSession, Session
    ```

- Client composition

    ```python title="Before"
    from skaha.client import SkahaClient

    client = SkahaClient(...)
    ```

    ```python title="After"
    from canfar.client import HTTPClient

    client = HTTPClient(...)
    ```

## Environment variables

```bash title="Before"
`SKAHA_TIMEOUT`, `SKAHA_CONCURRENCY`, `SKAHA_TOKEN`, `SKAHA_URL`, `SKAHA_LOGLEVEL
```
```bash title="After"
`CANFAR_TIMEOUT`, `CANFAR_CONCURRENCY`, `CANFAR_TOKEN`, `CANFAR_URL`, `CANFAR_LOGLEVEL`
```

## Configuration

- The default config file moves from `~/.skaha/config.yaml` to `~/.canfar/config.yaml`.
- The structure of the YAML file remains the same.

## Documentation and links

- Repo: `https://github.com/opencadc/canfar`
- Docs: `https://opencadc.github.io/canfar/`
- Changelog: `https://opencadc.github.io/canfar/changelog/`

## Notes on protocol stability

- Server base path segments under `/skaha` are server-side contracts and remain unchanged (for example, `https://ws-uv.canfar.net/skaha`).
- Historical header names remain unchanged (for example, `X-Skaha-Authentication-Type`, `X-Skaha-Registry-Auth`).

