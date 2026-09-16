<span id="legacy-cloud-platform-openstack-vms"></span>

# Legacy cloud workflows

This page is retained as a signpost for deployments that still operate the
older OpenStack-based CANFAR Cloud workflow. It is not the recommended path for
new research workloads. The current user-facing model is the [CANFAR Science
Platform](index.md): launch a Session from a Container Image and use mounted
storage or configured VOSpace Services.

<span id="modern-platform-advantages"></span>
<span id="when-to-use-legacy-platform"></span>
<span id="access-and-authentication"></span>
<span id="key-differences-from-digital-research-alliance-canada-defaults"></span>
<span id="registration-allocation"></span>
<span id="virtual-machine-management"></span>
<span id="creating-and-configuring-vms"></span>
<span id="1-create-a-vm"></span>
<span id="2-import-an-ssh-public-key"></span>
<span id="3-allocate-a-public-ip"></span>
<span id="4-launch-an-instance"></span>
<span id="5-connect-to-the-instance"></span>
<span id="vm-configuration-and-tools"></span>
<span id="pre-built-vm-helpers"></span>
<span id="system-maintenance"></span>
<span id="setting-up-batch-processing"></span>
<span id="1-create-a-vm_1"></span>
<span id="2-import-an-ssh-public-key_1"></span>
<span id="3-allocate-a-public-ip_1"></span>
<span id="4-launch-an-instance_1"></span>
<span id="5-connect-to-the-instance_1"></span>
<span id="install-software"></span>
<span id="test-on-the-vm"></span>
<span id="persist-results-to-vospace"></span>
<span id="snapshot-the-instance"></span>
<span id="automate-as-a-batch-script"></span>
<span id="write-a-submission-file"></span>
<span id="submit-jobs"></span>
<span id="extras-helpful-commands-vm-maintenance"></span>
<span id="option-2-hybrid-approach"></span>
<span id="modern-platform-documentation"></span>
<span id="platform-comparison"></span>

## If you already have a legacy VM

Follow the instructions supplied by the operator of that deployment for VM
creation, network access, firewall rules, quotas, and image selection. Those
values are deployment configuration and are not defined by the Python client
or CLI documentation in this repository.

Use the legacy VM only for work that depends on its existing environment. Keep
new scripts and data in a supported persistent location, and do not assume that
a VM path is mounted in a Science Platform Session.

<span id="migration-to-modern-platform"></span>
<span id="batch-processing-workflow"></span>
<span id="migration-strategies"></span>
<span id="option-1-containerise-your-workflow"></span>
<span id="option-3-gradual-migration"></span>
<span id="migration-resources"></span>
<span id="support-and-migration-assistance"></span>

## Moving a workflow to Sessions

1. Put the command and its dependencies in a [Container Image](containers/index.md).
2. Store persistent inputs and outputs under `/arc` or a VOSpace Service.
3. Use a Notebook or Desktop Session for exploration and a [headless Session](sessions/batch.md)
   for unattended commands.
4. Stage remote files to `/scratch` when a path-oriented program needs a local
   file, then copy results to persistent storage.

For deployment and operator documentation, see [OpenCADC Deployments](https://www.opencadc.org/deployments/).
For help choosing a supported workflow, contact [CANFAR support](support/index.md).
