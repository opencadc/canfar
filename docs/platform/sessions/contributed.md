# Contributed applications

Contributed Sessions expose community-provided web applications through the
Science Platform. The catalogue, image names, ports, and access requirements
are deployment-specific.

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

## Contribute an application

Start with a container that can run the application without interactive setup.
The platform operator must confirm the web endpoint, health check, command,
resource needs, image registry, and security requirements for the target
deployment. Do not assume a fixed port or startup path from another
application.

For the image workflow, see [Container Images](../containers/index.md) and
[Container Registry](../containers/registry.md). Contact
[support@canfar.net](mailto:support@canfar.net) before requesting that an image
be added to the catalogue.

## Related guides

- [Sessions overview](index.md)
- [Storage](../storage/index.md)
- [Permissions](../permissions.md)
- [Support](../support/index.md)
