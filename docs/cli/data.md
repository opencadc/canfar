# Data commands

Use `canfar data` to work with configured VOSpace Services and the local
filesystem through the embedded `fsspec-cli` command application.

## Install and authenticate

Data commands are included in the standard installation:

```bash
pip install canfar
canfar login cadc
```

CANFAR installs the audited upstream releases as normal dependencies through
immutable Git references:

- `vosfs @ git+https://github.com/shinybrar/vosfs@v0.6.0`
- `fsspec-cli @ git+https://github.com/shinybrar/vosfs@fsspec-cli-v0.5.0#subdirectory=src/fsspec-cli`

There is no separate data extra.

## Address mapped sources

Every remote source uses its configured Storage Name. The reserved `local`
source addresses the machine where the command runs. Operands always use an
explicit mapped name and absolute path:

```text
Storage-Name:/absolute/path
local:/absolute/path
```

For a default CADC login, the discovered primary Storage Name is `canfar`:

```bash
canfar data ls -lh canfar:/
canfar data ls -lh canfar:/folder
```

Use `ls -lh` (or `ll -h`) for a human-readable long listing. Standalone
`ls -h` is not supported. Empty `:/path`, bare local paths, `active:/path`, and
the retired `canfar storage` command are not aliases.

## Copy files and directories

Copy one file between local and remote sources:

```bash
canfar data cp local:/absolute/path/file.fits canfar:/folder/file.fits
canfar data cp canfar:/folder/file.fits local:/absolute/path/file.fits
```

Recursive copy is enabled for admitted local and remote source pairs:

```bash
canfar data cp -R local:/absolute/path/dataset canfar:/folder/dataset
```

The tagged upstream implementation builds a bounded manifest, copies files
through host-local staging when sources differ, and verifies destination
metadata. Recursive copy is not atomic and does not create a snapshot; inspect
the destination before removing any source data.

## Move data between sources

Cross-source `mv` is unsupported. Move a file explicitly by copying it,
verifying the destination, and only then issuing a separate source removal. In
this example, `archive` stands for a second Storage Name that you configured:

```bash
canfar data cp canfar:/folder/file.fits archive:/folder/file.fits
canfar data ls -lh archive:/folder/file.fits
canfar data rm canfar:/folder/file.fits
```

Do not use this sequence as a one-command or atomic move. CANFAR does not
advertise same-source `mv` for current VOSpace sources either.

Recursive removal is disabled by application policy. `rm -R` exits with status
2 and reports:

```text
rm: recursive removal disabled by application
```

Because directory removal is disabled, directory movement is not a supported
workflow in this release. Any future one-command relocation would be a
separately named, opt-in orchestration feature with stronger destination
verification and residual-state semantics—not portable `mv`.

## Output and accepted omissions

Data command stdout belongs to the embedded command; CANFAR does not prepend
the active-Server banner or add JSON/YAML envelopes. Diagnostics are written to
stderr.

This release intentionally provides no public CANFAR storage Python API, FUSE
mount, signed-URL extension, progress display, confirmation prompt, `:/path` or
bare-path shorthand, `active` alias, `canfar storage` alias, recursive removal,
or cross-source/current-VOSpace `mv` workflow.

## Audited upstream releases

CANFAR's integration is based on
[`shinybrar/vosfs` PR #294](https://github.com/shinybrar/vosfs/pull/294),
audited at commit
[`9e5314db4706894d31d54d245392f43b9556cfbb`](https://github.com/shinybrar/vosfs/commit/9e5314db4706894d31d54d245392f43b9556cfbb).
The installed pair is the tagged
[`vosfs` v0.6.0](https://github.com/shinybrar/vosfs/releases/tag/v0.6.0) and
[`fsspec-cli-v0.5.0`](https://github.com/shinybrar/vosfs/releases/tag/fsspec-cli-v0.5.0)
releases. CANFAR tests its composition, configuration, authentication, and
output seams; exhaustive filesystem-command and backend matrices remain in the
upstream project.
