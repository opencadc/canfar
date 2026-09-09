# Firefly Sessions

[Firefly](https://github.com/Caltech-IPAC/firefly) is a browser-based
astronomy application for viewing images, tables, and supported archive data.
The available Firefly image and features are deployment-specific.

## Launch Firefly

1. Sign in to the [Science Portal](https://www.canfar.net/science-portal/).
2. In **Launch New Session**, choose **Firefly**, select an image containing
   the software you need, and launch the Session.
3. Wait for it to start under **Active Sessions**, then open its application link.

Save your work under `/arc` before using the Session's delete control in the
portal. Closing the browser tab does not stop the Session. See
[Get started](../get-started.md) for account, storage, and cleanup steps.

### Launch from the command line (optional)

[Install the client](../../client/get-started.md#install) before using these commands.

```bash
canfar login cadc
canfar image ls --kind firefly
canfar create firefly IMAGE_NAME --name archive-exploration
```

The Science Portal provides the same Session Kind. Monitor the Session and
open it when ready:

```bash
canfar ps --all
canfar info SESSION_ID
canfar open SESSION_ID
```

If a Session remains `Pending`, inspect `canfar events SESSION_ID`; see [batch
troubleshooting](batch.md#monitor-and-troubleshoot).

## Load data

Use the paths and URLs supported by the selected Firefly image. A common
workflow is to place data under mounted storage:

```text
/arc/home/<user>/          personal persistent files
/arc/projects/<project>/   shared project files, when available
/scratch/                  temporary staging
```

For a remote object in a configured VOSpace Service, transfer it explicitly
before opening it in a path-oriented application:

```bash
canfar data cp IDENTIFIER:/path/to/image.fits local:/scratch/image.fits
```

Use Firefly's own archive or URL features only as documented by the selected
image. Do not assume that a VOSpace URL, archive endpoint, table format, or
remote service is enabled on every deployment.

Save figures, tables, regions, and other products under `/arc` or a persistent
VOSpace Service. `/scratch` is deleted when the Session ends. See [Storage](../storage/index.md)
and [Data transfers](../storage/transfers.md).

## Typical workflow

1. Open a FITS image, table, or archive result supported by the image.
2. Inspect image metadata and WCS before interpreting the display.
3. Use the image, table, and catalogue tools provided by the selected Firefly
   version.
4. Export products and record the source path, image reference, and relevant
   display settings.

For analysis that must be rerun, use Python or a headless Session and keep
Firefly for visual inspection.

## Troubleshooting

- If the image is unavailable, check `canfar image ls --kind firefly` and ask
  the platform operator about the deployment's catalogue.
- If a local file does not open, verify its path and permissions or stage it
  to `/scratch` with `canfar data cp`.
- If a remote URL fails, confirm that the image supports that endpoint and
  that the Session can reach it; do not embed credentials in the URL.
- If the browser disconnects, check `canfar ps --all` and `canfar info` before
  restarting the Session.

See [Support](../support/index.md) when the cause remains unclear.
