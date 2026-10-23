# Upstream provenance

`canfar` depends on two upstream distributions that are **pinned to one commit
of `shinybrar/vostools`**, not to PyPI releases. Record the pin and its basis
here whenever it moves.

## Current pins

| Distribution | Version | Source |
| --- | --- | --- |
| `vosfs` | `0.11.0` | `git+https://github.com/shinybrar/vostools@d6e2a44e3433bcff2e8f61437f10f2ce9f902a72#subdirectory=libs/vosfs` |
| `fss-cli` | `0.10.0` | same commit, `subdirectory=libs/fss-cli` |

Verified on October 15, 2026. `fss-cli` is the renamed `fsspec-cli`
distribution: import it as `fss_cli`, and route the `fss_cli` logger. There is
no compatibility alias. The commit is past the `vosfs` 0.11.0 and `fsspec-cli`
0.10.0 tags from `shinybrar/vosfs`. It also pages `vosfs` container listings
that exceed the XML parse cap.

CANFAR imports `httpx2` and requires Authlib 1.8.0 or later, whose existing
`authlib.integrations.httpx_client` integration uses `httpx2`. `vosfs` 0.11.0
still declares and uses `httpx`, so the original package remains a transitive
dependency in `uv.lock`.

## Why this matters

- The source is a personal repository, so the usual PyPI ownership and
  yanking guarantees do not apply. Review the commit before moving a pin.
- `uv.lock` records the resolved commit, which is the real integrity anchor.
  The requirement names that commit because `shinybrar/vostools` has no
  package release tag for this pin.
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
  its import and logger are `fss_cli` (current).
