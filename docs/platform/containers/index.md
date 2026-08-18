# Container Images

A Container Image bundles the operating-system libraries, astronomy software,
and application entrypoint used by a Session. The image is the software
environment; the Session request supplies the Session Kind, resources, command,
and mounted storage.

## Choose an image

List images that support a Session Kind before creating a Session:

```bash
canfar image ls --kind notebook
canfar image ls --kind headless
canfar create notebook IMAGE_NAME --name analysis
```

The image list and Science Portal are authoritative for available names,
versions, and supported kinds. Examples in these docs are illustrative and may
not exist in every deployment. A private image also requires access to its
Container Registry project.

## Build time and run time

Build-time changes are part of the image and can be reproduced by anyone with
the Dockerfile and build inputs. Run-time changes inside a Session are not an
image release. Keep stable dependencies in the image and save scripts or
configuration under persistent `/arc` storage.

```dockerfile
FROM python:3.13-slim

RUN python -m pip install --no-cache-dir astropy numpy
COPY reduce.py /opt/workflow/reduce.py
ENTRYPOINT ["python", "/opt/workflow/reduce.py"]
```

The base image, packages, and entrypoint must match the Session Kind. A
`headless` image must provide the command that the batch request invokes; a
Notebook or application image must provide the application expected by its
Session launcher.

## Runtime storage

When the deployment provides them, Sessions mount persistent `/arc` paths and
ephemeral `/scratch` storage. The image does not own those data lifetimes:

```text
/arc/home/<user>                 persistent personal files
/arc/projects/<project>         persistent shared project data
/scratch                         Session-local staging and intermediates
```

Use `/scratch` for fast temporary work and copy results to `/arc` or a
persistent VOSpace Service before stopping the Session. See [Storage](../storage/index.md).

## Resource and security considerations

- Keep credentials out of Dockerfiles, image layers, and command arguments.
- Pin important dependencies and rebuild when security fixes are needed.
- Keep images small so pulls and startup do not dominate short workloads.
- Request only the CPU, memory, and GPU that measurements support.
- Test the exact image with a small input before launching replicas.

## Build and publish

Use the build toolchain documented by your registry or deployment. A generic
local workflow is:

```bash
docker build -t images.canfar.net/<project>/<image>:<tag> .
docker push images.canfar.net/<project>/<image>:<tag>
```

The registry project must grant the account permission to push. Use a stable
version tag for reproducible workflows and reserve moving tags such as `latest`
for development. See [Building Containers](build.md) and [Registry](registry.md).

## Related guides

- [Building Containers](build.md)
- [Container Registry](registry.md)
- [Sessions](../sessions/index.md)
- [Batch processing](../sessions/batch.md)
