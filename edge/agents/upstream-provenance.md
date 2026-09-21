# Upstream provenance

`canfar` depends on two upstream distributions that are **pinned to tagged Git
refs on a personal fork**, not to PyPI releases. Record the pin and its basis
here whenever it moves.

## Current pins

| Distribution | Pin | Source |
| --- | --- | --- |
| `vosfs` | `v0.8.0` | `git+https://github.com/shinybrar/vosfs@v0.8.0` |
| `fsspec-cli` | `fsspec-cli-v0.7.0` | same repository, `subdirectory=src/fsspec-cli` |

## Why this matters

- The source is a personal repository, so the usual PyPI ownership and
  yanking guarantees do not apply. Review the tag before moving a pin.
- Tags are immutable by convention only. `uv.lock` records the resolved commit,
  which is the real integrity anchor.
- `vosfs` v0.8.0 added HTTP `Range` support, honoured by the `vault` byte
  endpoint and not by Cavern behind `arc`. Behaviour therefore differs per
  Storage Identifier; see [Data Access](../client/data.md).

## History

- `v0.6.0` / `fsspec-cli-v0.5.0` — first integration, audited at upstream
  PR #294, commit `9e5314db4706894d31d54d245392f43b9556cfbb`.
- `v0.7.0` / `fsspec-cli-v0.6.0` — Typer-owned commands, a breaking upstream
  change to command parsing.
- `v0.8.0` / `fsspec-cli-v0.7.0` — server-side `Range` support (current).
