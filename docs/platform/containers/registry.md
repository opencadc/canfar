# Container Registry

A Container Image is pulled from the registry named by its image reference.
The Science Platform may provide public images and project-scoped private
images; availability and permissions are deployment-specific. Use the image
listing and the project’s published instructions as the source of truth.

## Find an image

List images before creating a Session:

```bash
canfar image ls
canfar image ls --kind headless
```

Use the complete image reference returned by that command. Keep a stable tag
or digest in reproducible workflows rather than relying on `latest`.

## Publish an image

Container builds and registry credentials are controlled by the deployment.
When a project gives you a registry endpoint, use the standard container tools
with that endpoint and follow its access instructions:

```bash
docker build -t REGISTRY/PROJECT/IMAGE:TAG .
docker push REGISTRY/PROJECT/IMAGE:TAG
```

Do not put passwords or access tokens in a Dockerfile, an image layer, a
notebook, or a Session command. Prefer a short-lived credential mechanism
provided by the registry operator.

## Image contents

Keep images small and reproducible. Pin operating-system and language-package
inputs where practical, remove build-only material from runtime layers, and
run the image as a non-root user when the workload permits. Store data in
Science Platform storage rather than baking project data into an image.

The registry does not make a container a Session: [create a Session](../sessions/index.md)
with an image that the target Science Platform Server can pull.

## Troubleshooting

- A `not found` or pull error usually means the image reference is wrong, the
  tag was removed, or the target server cannot reach that registry.
- A private image may require project membership or a server-specific login.
- A successful push does not guarantee that every Science Platform deployment
  can pull the image.
- For a `Pending` Session, inspect `canfar info SESSION_ID` and
  `canfar events SESSION_ID` before changing the resource request.

See [container builds](build.md), [Session troubleshooting](../sessions/batch.md#monitor-and-troubleshoot),
and [support](../support/index.md).
