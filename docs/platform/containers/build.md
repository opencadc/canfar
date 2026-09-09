# Build a Container Image

Build a custom image when the required software is not available in an image
listed by the Science Portal. Keep the Dockerfile, dependency declarations, and
entrypoint in a version-controlled repository so another researcher can rebuild
the same environment.

## Before you build

1. Check `canfar image ls` for an existing image that already contains the
   required tools.
2. Decide which Session Kind will run the image: Notebook, Desktop, a
   contributed application, or `headless`.
3. Test the smallest useful workflow and identify persistent input/output paths.
4. Keep credentials, certificates, and research data outside the build context.

## Minimal Dockerfile

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN python -m pip install --no-cache-dir astropy numpy pandas
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

COPY workflow.py /opt/workflow/workflow.py
ENTRYPOINT ["python", "/opt/workflow/workflow.py"]
```

Use a base image appropriate to the software and architecture you need. The
example is a generic Python image, not a promise that it is the best base for a
particular astronomy application. Follow upstream licensing and installation
instructions for CASA, GPU libraries, and other system packages.

## Keep the image reproducible

- Pin important Python and system dependencies where practical.
- Keep one logical installation in each build layer and remove package caches.
- Use `.dockerignore` to exclude `.git`, datasets, local environments, and test
  output.
- Avoid `latest` in a production pipeline; record the immutable digest or a
  version tag used for the run.
- Run the image as a non-root user when the base image and application support
  it.

Do not bake a CADC certificate, bearer token, private key, or password into an
image. Supply runtime credentials through the supported authentication flow or
the deployment's secret mechanism.

## Test locally

Build and run a small smoke test before pushing:

```bash
docker build -t canfar-workflow:test .
docker run --rm canfar-workflow:test --help
```

For a `headless` image, test the exact command passed after the CLI `--`
delimiter. For an interactive image, confirm that the expected application
starts in the chosen Session Kind. The image cannot be validated solely by a
successful build.

## Publish and launch

Log in to the Container Registry using its documented credentials, then push a
versioned tag:

```bash
docker tag canfar-workflow:test images.canfar.net/<project>/workflow:0.1.0
docker push images.canfar.net/<project>/workflow:0.1.0
```

Confirm that the image is visible to the account that will launch it, then use
the exact published name:

```bash
canfar image ls
canfar create headless images.canfar.net/<project>/workflow:0.1.0 \
  -- python /arc/projects/<project>/run.py
```

The image project and tag are deployment data. Replace the placeholders and do
not copy an example registry path unchanged.

## Storage and runtime behavior

The image is not a data archive. In a Session, use mounted `/arc` paths for
persistent files and `/scratch` for temporary staging. A custom image should
not assume that a particular user's data, project, or VOSpace path exists.

For remote VOSpace data, use `canfar data` or the explicit
`canfar.storage.filesystem(identifier)` helper and stage path-oriented inputs
to `/scratch`. See [Storage](../storage/index.md).

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Build cannot install a dependency | Confirm the base image architecture, package name, and upstream installation instructions. |
| Image starts but command is missing | Test the entrypoint and command locally; check the Session Kind. |
| Pull is denied | Confirm the image name and project membership/registry credentials. |
| Session remains Pending | Check `canfar events SESSION_ID`; image pull and resource admission happen after creation. |
| Data is missing | Use a mounted `/arc` path or an explicit transfer; image layers do not contain Session storage. |

## Related guides

- [Container Images](index.md)
- [Registry](registry.md)
- [Batch processing](../sessions/batch.md)
- [Storage](../storage/index.md)
