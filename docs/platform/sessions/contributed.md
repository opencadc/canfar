# Contributed applications

Contributed Sessions expose community-provided web applications, such as
browser-based editors and reactive notebooks, through the Science Platform.
The catalogue of images is deployment-specific; the contract an image must
meet is the same everywhere and is described under
[Contribute an application](#contribute-an-application).

<span id="getting-started"></span>
<span id="troubleshooting"></span>
<span id="whats-next"></span>

## Launch an application

1. Sign in to the [Science Portal](https://www.canfar.net/science-portal/).
2. In **Launch New Session**, choose **Contributed**, select an image containing
   the software you need, and launch the Session.
3. Wait for it to start under **Active Sessions**, then open its application link.

Save your work under `/arc` before using the Session's delete control in the
portal. Closing the browser tab does not stop the Session. See
[Get started](../get-started.md) for account, storage, and cleanup steps.

### Launch from the command line (optional)

[Install the client](../../client/get-started.md#install) before using these commands.

List the images currently available for this Session Kind:

```bash
canfar login cadc
canfar image ls --kind contributed
canfar create contributed IMAGE_NAME --name my-application
```

Open the Session when it is ready. If it remains Pending, use the checks in
[batch troubleshooting](batch.md#monitor-and-troubleshoot). If it is Running
but the application page is unavailable, report the Session ID and image
reference to the platform operator.

## Data and persistence

Use the storage paths supplied by your project. Save inputs, notebooks, and
results under `/arc/home/<user>/`, `/arc/projects/<project>/`, or a configured
VOSpace Service. Use `/scratch` only for temporary files; it is not a durable
application workspace.

The application may have its own file picker or path conventions. Confirm the
path with the application documentation rather than assuming that every
contributed image exposes the same directories.

<span id="contributing-your-app"></span>

## Contribute an application

A contributed image is a web application that meets this contract:

| Requirement | Detail |
| --- | --- |
| Listen on port 5000 | Serve plain HTTP on TCP port 5000, on all interfaces. The Server checks that port to decide the Session is ready and healthy, and routes the browser to it. |
| Start by itself | The Server sets no command. The image's own `ENTRYPOINT` or `CMD` must start the application without interactive setup. |
| Run as any user | The container starts as the Session owner's user and group IDs, never as root, with every Linux capability dropped and privilege escalation off. Keep runtime files in locations that user can write, such as the home directory or `/tmp`. |
| Provide a shell | The Server runs `/bin/sh` and `cp` from the image while it prepares the Session's user and group files. |
| Tolerate a URL prefix | The browser opens `https://HOST/session/contrib/SESSION_ID/`. The Server strips that prefix, so the application receives requests at `/`. Use relative links, or a configurable base URL, so pages and assets still load from the prefixed address. |

Within those limits the application sees the same environment as other
Sessions: `HOME` is the user's persistent home directory, `/scratch` and the
project directories are mounted, and `OMP_NUM_THREADS` and the matching
thread variables are set to the requested core count.

Test the image as an unprivileged user before publishing it:

```bash
docker run --rm --user 12345:12345 --cap-drop ALL -p 5000:5000 IMAGE
```

Then push it to a registry the Server trusts and label it `contributed`, so
it is listed for this Session Kind; see
[Container Images](../containers/index.md#what-a-server-requires-of-an-image)
and [Container Registry](../containers/registry.md). Contact
[support@canfar.net](mailto:support@canfar.net) to have an application added
to the shared catalogue.

## Related guides

- [Sessions overview](index.md)
- [Storage](../storage/index.md)
- [Permissions](../permissions.md)
- [Support](../support/index.md)
