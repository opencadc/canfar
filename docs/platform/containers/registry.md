<span id="harbor-container-registry"></span>

# Container Registry

A Container Image is pulled from the registry named by its image reference.
The Science Platform may provide public images and project-scoped private
images; availability and permissions are deployment-specific. Use the image
listing and the project’s published instructions as the source of truth.

<span id="harbor-registry-overview"></span>
<span id="what-is-harbor"></span>
<span id="canfar-harbor-instance"></span>
<span id="repository-management"></span>
<span id="understanding-repositories"></span>
<span id="repository-naming"></span>
<span id="tagging-strategy"></span>
<span id="semantic-versioning"></span>
<span id="date-based-versioning"></span>
<span id="feature-and-environment-tags"></span>
<span id="managing-image-metadata"></span>
<span id="web-interface-access"></span>
<span id="harbor-web-interface"></span>
<span id="navigation-and-features"></span>
<span id="repository-view"></span>
<span id="image-details"></span>
<span id="basic-image-operations"></span>
<span id="registry-maintenance"></span>
<span id="monitoring-and-analytics"></span>
<span id="usage-statistics"></span>
<span id="audit-logging"></span>
<span id="backup-and-disaster-recovery"></span>
<span id="exportimport-procedures"></span>
<span id="best-practices"></span>
<span id="registry-best-practices"></span>
<span id="registry-organization"></span>
<span id="naming-conventions"></span>
<span id="network-optimization"></span>
<span id="integration-with-canfar-services"></span>

## Find an image

List images before creating a Session:

```bash
canfar image ls
canfar image ls --kind headless
```

Use the complete image reference returned by that command. Keep a stable tag
or digest in reproducible workflows rather than relying on `latest`.

<span id="projects-and-organization"></span>
<span id="project-structure"></span>
<span id="project-types"></span>
<span id="public-projects"></span>
<span id="private-projects"></span>
<span id="project-creation-and-management"></span>
<span id="requesting-new-projects"></span>
<span id="project-membership-management"></span>
<span id="access-control-and-security"></span>
<span id="authentication-methods"></span>
<span id="docker-cli-authentication"></span>
<span id="api-access"></span>
<span id="permission-matrix"></span>
<span id="project-dashboard"></span>
<span id="cli-and-api-usage"></span>
<span id="harbor-cli-operations"></span>
<span id="docker-registry-v2-api"></span>
<span id="automated-workflows"></span>
<span id="cicd-integration"></span>
<span id="automated-scanning-and-deployment"></span>
<span id="automated-retention-policies"></span>
<span id="authentication-integration"></span>

## Publish an image

Container builds and registry credentials are controlled by the deployment.
When a project gives you a registry endpoint, use the standard container tools
with that endpoint and follow its access instructions:

```bash
docker build -t REGISTRY/PROJECT/IMAGE:TAG .
docker push REGISTRY/PROJECT/IMAGE:TAG
```

After the push, label the image in the registry with each Session Kind it
supports (`notebook`, `headless`, `contributed`, and so on). The Science
Platform Server lists an image for a Kind only when it carries that label, and
picks up new labels on its next refresh; see
[what a Server requires of an image](index.md#what-a-server-requires-of-an-image).

Do not put passwords or access tokens in a Dockerfile, an image layer, a
notebook, or a Session command. Prefer a short-lived credential mechanism
provided by the registry operator.

<span id="vulnerability-scanning"></span>
<span id="scanning-process"></span>
<span id="vulnerability-reports"></span>
<span id="addressing-vulnerabilities"></span>
<span id="storage-management"></span>
<span id="repository-cleanup"></span>
<span id="performance-optimization"></span>
<span id="registry-performance"></span>
<span id="storage-integration"></span>
<span id="large-image-size"></span>

## Image contents

Keep images small and reproducible. Pin operating-system and language-package
inputs where practical, remove build-only material from runtime layers, and
run the image as a non-root user when the workload permits. Store data in
Science Platform storage rather than baking project data into an image.

The registry does not make a container a Session: [create a Session](../sessions/index.md)
with an image that the target Science Platform Server can pull.

<span id="common-issues"></span>
<span id="authentication-problems"></span>
<span id="pushpull-failures"></span>
<span id="vulnerability-scan-issues"></span>
<span id="performance-issues"></span>
<span id="slow-pushpull-operations"></span>

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
