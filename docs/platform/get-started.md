# Get started

The CANFAR Science Platform combines authenticated compute, Container Images,
and research storage. Start with the portal for interactive work, or install
the Python client and CLI for repeatable workflows.

## 1. Get an account and access

Request a [CADC account](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html)
and join the project or group that owns the data you need. Group membership
controls access to shared project paths and private Container Images. If you
need help, contact [CANFAR support](support/index.md).

## 2. Launch a first Session

From the [Science Portal](https://www.canfar.net/), select a Session Kind and
Container Image, then launch the Session. Start with a Notebook for Python
exploration; choose Desktop, CARTA, or Firefly when the workflow needs a
specialized interface. Use `headless` for a command that should run without an
interactive interface.

The portal's image list is authoritative for available images. Do not assume
that an example tag in this guide is published by every deployment.

## 3. Install the client (optional)

Install the released package on the machine from which you want to manage
Sessions or transfer data:

```bash
python -m pip install --upgrade canfar
canfar login cadc
canfar auth show
canfar server ls
```

The CLI stores Authentication Records and discovered Science Platform Servers
in its local configuration. See the [CLI reference](../cli/cli-help.md) and
[Python client guide](../client/get-started.md).

## 4. Put data in the right place

Inside a Session, use mounted paths when they are available:

| Location | Use |
| --- | --- |
| `/arc/home/<user>` | Personal scripts and results |
| `/arc/projects/<project>` | Shared project data and outputs |
| `/scratch` | Temporary staging and intermediates; deleted with the Session |

For remote data, use [canfar data](storage/transfers.md) or
`canfar.storage.filesystem(identifier)` in Python. Storage Identifiers are
explicit configuration names; do not invent a `vault://` URL or import a
configured identifier as a Python attribute.

## 5. Run and preserve a workflow

1. Test the command on a small input in an interactive Session.
2. Write a durable input/output path into the command or environment.
3. Submit a [headless Session](sessions/batch.md) for unattended work.
4. Inspect `Pending` Sessions with `canfar ps --all`, `canfar info`, and
   `canfar events`.
5. Copy final results out of `/scratch` before deleting the Session.

## Next steps

- [Platform concepts](concepts.md)
- [Sessions](sessions/index.md)
- [Storage](storage/index.md)
- [Containers](containers/index.md)
- [Permissions](permissions.md)
- [Support](support/index.md)
