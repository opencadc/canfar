# Legacy cloud workflows

This page is retained as a signpost for deployments that still operate the
older OpenStack-based CANFAR Cloud workflow. It is not the recommended path for
new research workloads. The current user-facing model is the [CANFAR Science
Platform](index.md): launch a Session from a Container Image and use mounted
storage or configured VOSpace Services.

## If you already have a legacy VM

Follow the instructions supplied by the operator of that deployment for VM
creation, network access, firewall rules, quotas, and image selection. Those
values are deployment configuration and are not defined by the Python client
or CLI documentation in this repository.

Use the legacy VM only for work that depends on its existing environment. Keep
new scripts and data in a supported persistent location, and do not assume that
a VM path is mounted in a Science Platform Session.

## Moving a workflow to Sessions

1. Put the command and its dependencies in a [Container Image](containers/index.md).
2. Store persistent inputs and outputs under `/arc` or a VOSpace Service.
3. Use a Notebook or Desktop Session for exploration and a [headless Session](sessions/batch.md)
   for unattended commands.
4. Stage remote files to `/scratch` when a path-oriented program needs a local
   file, then copy results to persistent storage.

For deployment and operator documentation, see [OpenCADC Deployments](https://www.opencadc.org/deployments/).
For help choosing a supported workflow, contact [CANFAR support](support/index.md).
