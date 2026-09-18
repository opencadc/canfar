# Move and read data

Every operand is a **Storage Identifier** followed by an absolute path:
`arc:/home/USER/file.fits`. `local` is the machine running the command. `arc`
and `vault` are the default CADC identifiers; list the ones this user has with
`canfar server ls -o json` (each Server's `storage` keys) or
`canfar.storage.identifiers()`.

Inside a Session, data already under `/arc` is read by its POSIX path with
ordinary tools: on CADC, `arc:/projects/PROJECT/x` is `/arc/projects/PROJECT/x`
there. Use the commands below from a laptop, or for a service the Session
does not mount.

From outside a Session, the routes into ARC are these commands and Storage
Management in the browser; the older SSHFS instructions are retired.

## Credentials follow the storage, not the compute

Each remote identifier uses the Identity Provider of the Server that owns it,
independently of the active Server Selection. Default `arc` and `vault` need
CADC credentials (`canfar login cadc`, handed to the user) even when compute
runs on SRCNet. Data commands see every configured identifier.

## Shell

```bash
canfar data ls -lh arc:/home/USER
canfar data cp local:/absolute/input.fits arc:/projects/PROJECT/input.fits
canfar data cp -R local:/absolute/run-42 vault:/PROJECT/runs/run-42
canfar data mkdir -p arc:/projects/PROJECT/results
canfar data info arc:/projects/PROJECT/input.fits
```

`canfar data --help` lists the installed commands (`ls`, `ll`, `du`, `find`,
`tree`, `head`, `tail`, `cat`, `cp`, `mv`, `mkdir`, `rmdir`, `unlink`, `rm`,
and more). The data application owns its stdout, so read its text output.
`cp -R` copies a directory. `mv` works within one identifier, and `rm` takes
files one at a time: to move between identifiers or clear a tree, copy, verify
the destination with `info` or `ls`, then remove what the user authorized.

Transfer is done when the destination is **verified**: it lists with the
expected size.

## Python

```python
from canfar.storage import filesystem, identifiers

print(identifiers())
vault = filesystem("vault")
try:
    vault.get_file("/REMOTE/PATH/input.fits", "/LOCAL/PATH/input.fits")
finally:
    vault.close()
```

`filesystem(identifier)` returns a standard fsspec filesystem, so `ls`, `find`,
`info`, `get_file`, `put_file`, and `open` work as fsspec documents them. For a
listing a script will parse, such as a batch manifest, use `find(path)`, which
returns a list of paths, where the shell commands print text for people.
`filesystem("local")` needs no Authentication Record. Opening a remote object
can transfer the whole file, so for a tool that needs a filename, or for
repeated reads, stage one copy with `get_file()` (to `/scratch` in a Session)
and work on that.

Staging, caching, and scientific-library recipes are in
[Data access](https://www.opencadc.org/canfar/edge/client/data/) and
[Filesystem and Python tools](https://www.opencadc.org/canfar/edge/platform/storage/filesystem/);
command details in [Data commands](https://www.opencadc.org/canfar/edge/cli/data/);
browser uploads and downloads in
[Data transfers](https://www.opencadc.org/canfar/edge/platform/storage/transfers/);
sharing and legacy `vos` tools in
[VOSpace](https://www.opencadc.org/canfar/edge/platform/storage/vospace/).
