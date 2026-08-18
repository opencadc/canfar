# Data transfers

Use `canfar data` for authenticated transfers between configured VOSpace
Services and the local filesystem. The command is the shell front door for the
same Storage Identifier mapping used by `canfar.storage`.

## Operand syntax

Every operand is an explicit Storage Identifier followed by an absolute path:

```text
identifier:/absolute/path
```

`local` is always available and means the machine where `canfar` is running.
Configured names such as `arc` or `vault` are deployment data; list the names
with the configuration tools or use the names shown in your setup. The embedded
application does not register those names as Python or fsspec protocols.

```bash
canfar data ls -lh local:/tmp
canfar data ls -lh vault:/project
canfar data ls -lh arc:/projects/<project>
```

Authentication and endpoint resolution happen when the command opens a
configured source. If a credential is missing or expired, log in to the
corresponding Identity Provider and retry.

## Inspect data

```bash
canfar data ls -lh vault:/project
canfar data info vault:/project/catalog.csv
canfar data size vault:/project/catalog.csv
canfar data stat vault:/project/catalog.csv
canfar data find vault:/project --type f
```

Use `canfar data --help` and the individual command help for the complete
upstream fsspec-cli surface. The command output is intentionally owned by that
application; CANFAR does not add an active-server banner to it.

## Copy files and directories

Copy one file in either direction:

```bash
canfar data cp local:/data/result.fits vault:/project/results/result.fits
canfar data cp vault:/project/input.fits local:/scratch/input.fits
```

Use `-R` (or `-r`) for a directory copy:

```bash
canfar data cp -R local:/data/run-42 vault:/project/runs/run-42
```

Create a destination first when that makes the workflow clearer:

```bash
canfar data mkdir -p vault:/project/results
canfar data cp local:/scratch/result.fits vault:/project/results/result.fits
```

For a transfer between two remote VOSpace Services, use an explicit copy and
verify the destination. Do not assume that a cross-source `mv` is supported:

```bash
canfar data cp vault:/project/input.fits arc:/projects/<project>/input.fits
canfar data info arc:/projects/<project>/input.fits
```

The CLI keeps recursive removal disabled. Delete individual files with `rm` or
empty directories with `rmdir` only after checking the path:

```bash
canfar data rm vault:/project/results/old.fits
canfar data rmdir vault:/project/results/empty-directory
```

## Session workflow

Inside a Science Platform Session, prefer a mounted `/arc` path for data that is
already present there. For one remote input, copy directly to `/scratch`, run
the analysis locally, and copy final products to `/arc` or a persistent VOSpace
destination:

```bash
canfar data cp vault:/project/cube.fits local:/scratch/cube.fits
python reduce.py /scratch/cube.fits /scratch/result.fits
canfar data cp local:/scratch/result.fits arc:/projects/<project>/result.fits
```

`/scratch` is Session-local and is deleted when the Session ends. It is a good
staging location, not a backup. For repeated Python reads, select an explicit
fsspec whole-file cache under `/scratch`; see [Filesystem and Python tools](filesystem.md).

## Transfer failures

| Symptom | What to check |
| --- | --- |
| Unknown Storage Identifier | Use the configured identifier exactly; `local` is the only reserved name. |
| Authentication failure | Run the appropriate `canfar login <idp>` and confirm the saved Authentication Record. |
| Permission denied | Confirm the VOSpace path and project/group membership. |
| Destination is missing | Create parent directories with `canfar data mkdir -p`. |
| Copy is slow | Avoid many small remote reads; stage once to `/scratch` or use one explicit cache. |
| Files disappear after a Session | Move results from `/scratch` to `/arc` or a persistent VOSpace Service before deletion. |

For a service outage or persistent authorization issue, contact [CANFAR
support](../support/index.md).

## Related guides

- [Storage overview](index.md)
- [Filesystem and Python tools](filesystem.md)
- [VOSpace](vospace.md)
- [Permissions](../permissions.md)
