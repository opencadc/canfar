# Data transfers

Copy files between your computer and CANFAR storage in your browser, or use
`canfar data` for repeatable command-line transfers.

## Transfer files in your browser

Sign in to [Storage Management](https://www.canfar.net/storage/arc/list) with
your Canadian Astronomy Data Centre (CADC) account. You can also follow the
storage link from the Science Portal. Your personal directory is under
`home/USER`; shared data is under `projects/PROJECT`. Replace `USER` and
`PROJECT` with the names used by your account and project.

### Upload inputs

1. Navigate to the directory where you want the files to remain, such as your
   personal directory or a project directory where you have write access.
2. Select **Add**, choose the file or folder upload option, and select the
   items from your computer. Follow the upload dialog to start the transfer.
3. Wait for completion, refresh the directory listing, and check that the
   expected filenames and sizes appear before opening them in a Session.

A file uploaded to `home/USER/input.fits` is available inside a Session as
`/arc/home/USER/input.fits`. For shared directories, ask your project
administrator for access; see [Permissions](../permissions.md).

### Download results

1. Navigate to the directory containing the results and select the files or
   folders you need.
2. Open the download action. Choose **Zip** to download the selected data as
   an archive. **URL List** and **HTML List** produce lists of links, rather
   than an archive containing the data.
3. Save the download to your computer. Open the archive or a downloaded file
   to confirm that you have the expected results.

Links to private data still require authentication. For scripted transfers,
use the authenticated CLI workflow below.

## Transfer files from a terminal

[Install the client](../../client/get-started.md#install) and log in to the
identity provider that owns the storage service. The default `arc` and `vault`
services use CADC credentials (`canfar login cadc`), independently of which
server you selected for compute.

### Operand syntax

Every operand is an explicit Storage Identifier followed by an absolute path:

```text
identifier:/absolute/path
```

`local` is always available and means the machine where `canfar` is running.
Configured names such as `arc` or `vault` are deployment data; list the names
with the configuration tools or use the names shown in your setup. These names identify storage locations in your CANFAR configuration.

```bash
canfar data ls -lh local:/tmp
canfar data ls -lh vault:/project
canfar data ls -lh arc:/projects/PROJECT
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
canfar data cp vault:/project/input.fits arc:/projects/PROJECT/input.fits
canfar data info arc:/projects/PROJECT/input.fits
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
canfar data cp local:/scratch/result.fits arc:/projects/PROJECT/result.fits
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
