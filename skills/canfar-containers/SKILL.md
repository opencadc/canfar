---
name: canfar-containers
description: >
  CANFAR Container Images and registries: discover images allowed by Skaha,
  choose reproducible environments, use CADC Harbor when applicable, build team
  images, and satisfy the contributed-app port 5000 contract. Use when picking
  or publishing an image, using Harbor, writing a Dockerfile, or contributing
  an application.
---
# Container Images and registries

User guide: [Containers](https://www.opencadc.org/canfar/latest/platform/containers/)

## Choose from the live Skaha catalog

The Science Portal and Skaha image API list Container Images the user is allowed
to launch:

```bash
canfar image ls
canfar image ls --kind notebook
```

Registry hosts are deployment-configured. CADC uses
[images.canfar.net](https://images.canfar.net); another site can allow one or
several different hosts.

```bash
canfar create notebook images.canfar.net/skaha/astroml:latest
```

Two-part image names currently expand to `images.canfar.net/<name>` in the
`canfar` client. That is a CADC convenience, not deployment-neutral discovery.
Use the full URI returned by the selected Server when scripting across sites.

## What Skaha actually requires

- The image must come from an allowed `registryHosts` entry.
- Its registry metadata must make it visible for the requested Session kind.
- The container runs as the authenticated user's mapped UID/GID and receives the
  deployment's shared POSIX and scratch mounts.
- Notebook/Desktop/CARTA/Firefly/contributed use distinct Job templates and probe
  contracts; do not assume one image works for every kind.

## Custom images

1. Confirm an existing catalog image cannot satisfy the workflow.
2. Build from a suitable base and test as a non-root runtime user.
3. Push to the site's allowed Container Registry with the required project role
   and Skaha type metadata.
4. Confirm it appears in `canfar image ls --kind <kind>`.
5. Launch by the full image URI.

```bash
# CADC example path; substitute the site's persistent project mount.
canfar create headless images.canfar.net/mygroup/pipeline:1.0 \
  -- python /arc/projects/mygroup/run.py
```

## Contributed web applications

The current Skaha `launch-contributed.yaml` template exposes and probes TCP port
**5000**. It does not invoke `/skaha/startup.sh`; the image's own ENTRYPOINT/CMD
must start the web service. `/skaha/startup.sh` is used by the desktop-application
launcher and remains a different image convention.

This code-level contract supersedes older public guidance that required the
startup script for contributed apps.

## Optional Library Tools

`opencadc/canfar-library` provides an optional scientist-first `library` CLI for
manifest-driven `init → lint → build → scan → curate → push`. It is not a core
Skaha runtime and may not be installed or released on the user's site; check
`library --help` and its local version before recommending commands.

## Reproducibility and safety

1. Prefer a version tag or digest over `:latest`/`:dev` for production science.
2. Record the full image URI and ideally digest in workflow metadata and papers.
3. Do not put credentials, private keys, or user data into image layers.
4. Registry push permission and Skaha launch visibility are separate controls.

Related: `canfar-permissions`, `canfar-sessions`, `canfar-cvmfs`
