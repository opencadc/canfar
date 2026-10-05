# Upstream provenance

`canfar` depends on two upstream distributions that are **pinned to tagged Git
refs on a personal fork**, not to PyPI releases. Record the pin and its basis
here whenever it moves.

## Current pins

| Distribution | Pin | Source |
| --- | --- | --- |
| `vosfs` | `v0.11.0` | `git+https://github.com/shinybrar/vosfs@v0.11.0` |
| `fsspec-cli` | `fsspec-cli-v0.10.0` | same repository, `subdirectory=src/fsspec-cli` |

Verified on October 4, 2026. The lockfile resolves these tags to
`d7e2cbc5a5d121a2cc006796884452ad5ed7539c` and
`054cfd9e1cd68081d23578595a9c5c16f70dee60`, respectively.

CANFAR imports `httpx2` and requires Authlib 1.8.0 or later, whose existing
`authlib.integrations.httpx_client` integration uses `httpx2`. `vosfs` 0.11.0
still declares and uses `httpx`, so the original package remains a transitive
dependency in `uv.lock`.

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
- `v0.8.0` / `fsspec-cli-v0.7.0` — server-side `Range` support.
- `v0.9.0` / `fsspec-cli-v0.8.0` — upstream simplification of both packages.
- `v0.10.0` / `fsspec-cli-v0.9.0` — verified recursive-copy resumption and
  restored shell listings. Recursive copies skip a destination file
  only after matching content checksums or comparing staged bytes; size alone
  is insufficient. See [Data commands](../cli/data.md).
- `v0.11.0` / `fsspec-cli-v0.10.0` — per-file transfer logging and fewer
  requests for tree and bulk operations (current). See
  [Logging](../cli/logging.md).
