# Data commands

`canfar data` delegates to the embedded `fsspec-cli` command application. It
maps every configured VOSpace Service by its Storage Identifier and always
adds the reserved `local` source for the machine running the command.

## Sources and operands

Run `canfar login` for the IDP that owns a remote VOSpace Service, then use an
explicit source-qualified operand:

```text
storage-identifier:/absolute/path
local:/absolute/path
```

The default CADC configuration provides `arc`, `vault`, and `local` when its
default Server record is present:

```bash
canfar data ls -lh arc:/home/user
canfar data ls -lh vault:/
canfar data ls -lh local:/tmp
```

Storage Identifiers are configuration keys, not protocols. There is no
`active:/` source, bare local-path shorthand, empty `:/path` source, or
`canfar storage` command. A data command sees all configured sources, not only
the active Server Selection.

## Command surface

Use `canfar data --help` for the installed upstream options. The available
commands are:

| Command | Purpose |
| --- | --- |
| `basename`, `dirname` | Transform a path string. |
| `info`, `size`, `stat`, `test` | Inspect a file or evaluate a predicate. |
| `ls`, `ll` | List directory contents; `ls` accepts `-A`, `-l`, and `-h`, while `ll` accepts `-A` and `-h`. |
| `du` | Estimate file space usage; supports `-s` and `-h`. |
| `find`, `tree` | Traverse recursively; `find` supports `--maxdepth` and `--type f|d`, while `tree` supports `--maxdepth`. |
| `head`, `tail`, `cat` | Read leading bytes, trailing bytes, or file contents. |
| `cp` | Copy files or one directory; `-R`/`-r` enables recursive copy. |
| `mv` | Move or rename files on one mapped filesystem. |
| `mkdir`, `rmdir`, `unlink`, `rm` | Create directories, remove empty directories, remove one file, or remove files. |

Recursive removal is disabled by CANFAR policy, so `data rm` has no `-R` or
`-r` option. `data mv` does not implement a cross-source move; copy between
sources and verify the destination before removing the source separately.

## Examples

List and inspect a remote object:

```bash
canfar data ls -lh arc:/home/user
canfar data info arc:/home/user/file.fits
canfar data cat arc:/home/user/file.fits
```

Copy between local and remote sources:

```bash
canfar data cp local:/tmp/file.fits arc:/home/user/file.fits
canfar data cp arc:/home/user/file.fits local:/tmp/file.fits
```

Recursive copy is available for one directory and its descendants:

```bash
canfar data cp -R local:/tmp/dataset arc:/home/user/dataset
```

For a cross-source move, make the verification and removal explicit:

```bash
canfar data cp vault:/folder/file.fits arc:/home/user/file.fits
canfar data info arc:/home/user/file.fits
canfar data rm vault:/folder/file.fits
```

Data command stdout belongs to the embedded command. CANFAR does not prepend
the active-Server banner or add a JSON/YAML envelope, and data commands do not
provide the CANFAR `-o/--output` option.

For Python access, explicit `Storage Identifier` resolution and cache guidance
are documented in [Data Access](../client/data.md).
