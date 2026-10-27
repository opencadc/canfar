# Upstream provenance

`canfar` installs its storage dependencies from PyPI. Both distributions come
from [opencadc/fsspec-tools](https://github.com/opencadc/fsspec-tools).
Update this record when their requirements or sources change.

<span id="current-pins"></span>

## Current requirements

| Distribution | Required minimum | Locked version | Source |
| --- | --- | --- | --- |
| `vosfs` | `0.12.0` | `0.12.0` | [PyPI](https://pypi.org/project/vosfs/) |
| `fss-cli` | `0.11.1` | `0.11.1` | [PyPI](https://pypi.org/project/fss-cli/) |

Verified against `pyproject.toml`, `uv.lock`, and installed package metadata
on October 27, 2026. `fss-cli` is the renamed `fsspec-cli`
distribution: import it as `fss_cli`, and route the `fss_cli` logger. There is
no compatibility alias. Registry requirements replaced the former Git pin
in CANFAR v1.5.1.

CANFAR imports `httpx2` and requires Authlib 1.8.0 or later, whose existing
`authlib.integrations.httpx_client` integration uses `httpx2`. `vosfs` 0.12.0
still declares and uses `httpx`, so the original package remains a transitive
dependency in `uv.lock`.

## Why this matters

- `pyproject.toml` declares minimum versions. A new installation can resolve
  newer compatible releases.
- `uv.lock` records registry versions and artifact hashes. Use the lockfile
  to reproduce development installs and review upstream changes when updating it.
- `vosfs` v0.8.0 added HTTP `Range` support, honoured by the `vault` byte
  endpoint and not by Cavern behind `arc`. Behaviour therefore differs per
  Storage Identifier; see [Data Access](../client/data.md).

## History

- `v0.6.0` / `fsspec-cli-v0.5.0`: first integration, audited at upstream
  PR #294, commit `9e5314db4706894d31d54d245392f43b9556cfbb`.
- `v0.7.0` / `fsspec-cli-v0.6.0`: Typer-owned commands, a breaking upstream
  change to command parsing.
- `v0.8.0` / `fsspec-cli-v0.7.0`: server-side `Range` support.
- `v0.9.0` / `fsspec-cli-v0.8.0`: upstream simplification of both packages.
- `v0.10.0` / `fsspec-cli-v0.9.0`: verified recursive-copy resumption and
  restored shell listings. Recursive copies skip a destination file
  only after matching content checksums or comparing staged bytes; size alone
  is insufficient. See [Data commands](../cli/data.md).
- `v0.11.0` / `fsspec-cli-v0.10.0`: per-file transfer logging and fewer
  requests for tree and bulk operations. See
  [Logging](../cli/logging.md).
- `d6e2a44e3433bcff2e8f61437f10f2ce9f902a72`: both packages now come from
  `shinybrar/vostools`. The command library's distribution is `fss-cli` and
  its import and logger are `fss_cli`. This was the former Git source.
- CANFAR v1.5.1: switched to PyPI requirements for `vosfs>=0.12.0` and
  `fss-cli>=0.11.1` from `opencadc/fsspec-tools`.
