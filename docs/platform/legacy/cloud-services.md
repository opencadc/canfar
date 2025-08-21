# CANFAR Cloud Services {#cloud-services-overview}

!!! abstract "🎯 What You'll Learn"
    - What cloud services power CANFAR (via Digital Research Alliance Canada OpenStack)  
    - Differences between DRAC OpenStack cloud and CANFAR cloud access  
    - How to log in and manage credentials (CADC accounts vs DRAC accounts)  
    - Where to find the correct cloud portals (Arbutus, Arbutus-CANFAR)  
    - Best practices for using shared cloud allocation resources  

- All CANFAR cloud services are hosted on the Digital Research Alliance Canada (DRAC) OpenStack Infrastructure.  
- Access is integrated with CADC credentials and customized portals, ensuring consistency and security across CANFAR workflows.  
- When you request access, the CANFAR team will review it and arrange your registration with the DRAC.

For a typical workflow with OpenStack Cloud Services and batch processing on CANFAR, see the tutorial below.

## Key differences from DRAC defaults {#key-differences}
- **Credentials**: Sign in with **CADC Username/Password** (not a DRAC account).
- **Portal**: [:material-open-in-new: Use the arbutus-canfar portal](https://arbutus-canfar.cloud.computecanada.ca/) (instead of [arbutus](https://arbutus.cloud.computecanada.ca/)).
- **Resource policy**: interactive analysis gets reasonable quotas; **batch processing** can scale to large footprints.

## Registration & Allocation {#registration}
A CADC account is required to access cloud services.

1. Register a CADC account.
2. Email CANFAR support with:
    - Project Name
    - CADC Account `Username`
    - Estimated resources (storage, compute; whether you need batch)
    - A short description of your use case (2–3 sentences)

CANFAR will review and coordinate project/quotas on the DRAC side.

---

## Batch Tutorial {#batch-tutorial}
This tutorial builds a basic **source detection** pipeline for CFHT MegaCam images on a CANFAR VM with fast access to the CADC archive and VOSpace, that runs it on the CANFAR batch system.

!!! note "You will learn to"
    - Create/manage VMs on DRAC OpenStack / CANFAR
    - Access CADC VOSpace
    - Submit batch jobs that run your pipeline

!!! tip "Only need persistent (non-batch) VMs?"
    - If you just need persistent VMs, follow DRAC VM docs and skip the batch sections here.
    - Throughout the guide, `<USERNAME>` refers to your CADC username; `<VOSPACE>` maps to your VOSpace; `<PROJECT>` is the OpenStack Project.


## Create and Connect to a VM

### 1. Create a VM {#create-vm}
Use the DRAC web dashboard.

1. Sign in to [:material-open-in-new: Dashboard](https://arbutus-canfar.cloud.computecanada.ca/) with CADC `<USERNAME>`/password.
2. Each CANFAR allocation maps to an OpenStack **`<PROJECT>`**. Use the top-left project picker to switch if you belong to multiple.

Follow DRAC’s [Creating a Linux VM](https://docs.alliancecan.ca/wiki/Creating_a_Linux_VM). Summary below.

---

### 2. Import an SSH Public Key

OpenStack prefers SSH key pairs over passwords.

- If you do not have a key pair, run `ssh-keygen` locally or follow DRAC’s [SSH Keys documentation].
- In **Compute → Key Pairs**, click **Import Key Pair**.
- Name the key and paste your public key (default path `~/.ssh/id_rsa.pub`).

---

### 3. Allocate a Public IP

- Go to **Network → Floating IPs**.
- If none is listed, click **Allocate IP to Project**.
- Typically, each project has one public IP; if exhausted you’ll see _Quota Exceeded_.

---

### 4. Launch an Instance

- In **Compute → Instances → Launch Instance**, choose:
  - **Source**: _canfar-ubuntu-20.04_ (important for batch)
  - **Flavor**: e.g., `c2-7.5gb-30` (2 vCPU / 7.5 GiB RAM / ~31 GiB ephemeral disk)
  - **Key Pair**: select your SSH key
- Click **Launch**.

---

### 5. Connect to the Instance

After status becomes **Running**, first **associate** the floating IP (menu → **Associate Floating IP**), then SSH:

```bash
ssh ubuntu@<FLOATING_IP>
```

Create a local user matching your CADC account (for audit/minimal access):

```bash
sudo canfar_create_user <USERNAME>
logout
ssh <USERNAME>@<FLOATING_IP>
```

!!! note "Default image users"
    - Ubuntu images: `ubuntu`
    - Rocky Linux images: `rocky`

---

### Install software {#install-software}
The base VM image comes with only a minimal set of packages.  
For this example, we need to install two additional tools:

- [Source Extractor](https://sextractor.readthedocs.io/) (source detection): software used to detect astronomical sources in FITS images, producing catalogues of stars and galaxies.
- [funpack](https://heasarc.gsfc.nasa.gov/fitsio/fpack/) (FITS decompressor; Ubuntu package `libcfitsio-bin`)：a decompression utility for FITS images. Most FITS images provided by CADC are Rice-compressed and stored with an `.fz` extension. Since Source Extractor only accepts uncompressed images, we will use `funpack` to uncompress them. The `funpack` executable is distributed as part of the `libcfitsio-bin` package in Debian/Ubuntu.

Because both tools are available from the Ubuntu software repository, we can install them system-wide after updating the package index:
```bash title="Install packages"
sudo apt update -y
sudo apt install -y source-extractor libcfitsio-bin
```

### Test on the VM {#test-vm}
Use the ephemeral disk (mounted at `/mnt`) for scratch.

```bash
sudo canfar_setup_scratch  # create /mnt/scratch with proper permissions
cd /mnt/scratch
cp /usr/share/source-extractor/default* .
cat > default.param <<'EOF'
NUMBER
MAG_AUTO
X_IMAGE
Y_IMAGE
EOF
cadcget cadc:CFHT/1056213p.fits.fz
funpack -D 1056213p.fits.fz
source-extractor 1056213p.fits -CATALOG_NAME 1056213p.cat
```

!!! warning "Scratch space"
    - Run `canfar_setup_scratch` each time you boot a **new** instance.
    - In **batch mode**, each job gets its own scratch directory (not `/mnt/scratch`).

### Persist results to VOSpace {#persist-results}
Ephemeral storage is wiped when the VM terminates. Upload the output `1056213p.cat` to **VOSpace** (the VM includes the `vos` client).

Obtain a proxy certificate for automated access:

```bash
cadc_dotnetrc      # one-time helper to create ~/.netrc
cadc-get-cert -n   # generate an X509 proxy (default 10 days)
```

```bash
vcp 1056213p.cat vos:<VOSPACE>/
```

!!! danger "Credential hygiene"
    `.netrc` stores credentials in plaintext. Use only on controlled hosts and restrict permissions: `chmod 600 ~/.netrc`.

### Snapshot the instance {#snapshot}
In the **Instances** view, click **Create Snapshot** (e.g., name it `image-reduction-2023-08-21`).

!!! warning
    Avoid writes on the VM while a snapshot is being created.

Without a snapshot, **ephemeral** data is lost when the instance is deleted. **Volume-backed** VMs persist data but are **not suitable for batch**.

### Automate as a batch script {#batch-script}
CANFAR batch is powered by **HTCondor**; Cloud Scheduler launches worker VMs on demand.

Create `~/do_catalogue.bash`:

```bash
#!/usr/bin/env bash
set -euo pipefail
id="$1"
cadcget "cadc:CFHT/${id}.fits.fz"
funpack -D "${id}.fits.fz"
cp /usr/share/source-extractor/default* .
cat > default.param <<'EOF'
NUMBER
MAG_AUTO
X_IMAGE
Y_IMAGE
EOF
source-extractor "${id}.fits" -CATALOG_NAME "${id}.cat"
vcp "${id}.cat" "vos:<VOSPACE>/"
```

### Write a submission file {#submission}
Submit four image IDs: `1056215p 1056216p 1056217p 1056218p`.

```text title="do_catalogue.sub"
executable = do_catalogue.bash

output = do_catalogue-$(arguments).out
error  = do_catalogue-$(arguments).err
log    = do_catalogue-$(arguments).log

queue arguments from (
  1056215p
  1056216p
  1056217p
  1056218p
)
```

### Submit jobs {#submit}
Two authorizations are needed:
- Access to snapshots in `<PROJECT>`
- Write access to `<VOSPACE>`

On the batch login node `batch.canfar.net`:

```bash
ssh <USERNAME>@batch.canfar.net
. <PROJECT>-openrc.sh     # set OpenStack env (once per session)
```

Submit:

```bash
canfar_submit do_catalogue.sub image-reduction-2023-08-21 c2-7.5gb-30
```

Where:
- `do_catalogue.sub`: submission file
- `image-reduction-2023-08-21`: snapshot image name
- `c2-7.5gb-30`: VM flavor (list via `openstack flavor list`)

Monitor:

```bash
condor_q
condor_q -all   # all users summary
```

When the interactive VM is no longer needed, delete it from the dashboard (**Delete Instances**).

---

## Extras: helpful commands & VM maintenance {#extras}
- Keep the OS updated: `sudo apt update && sudo apt dist-upgrade` (or `dnf` on Rocky).
- Prebuilt VM helpers (`canfar-ubuntu-20.04` / `canfar-rocky-8`):
  - `cadc_cert -u <USERNAME>`: obtain a CADC proxy (legacy helper)
  - `cadc_dotnetrc`: create/update `~/.netrc`
  - `canfar_setup_scratch`: set up `/mnt/scratch`
  - `canfar_create_user <USERNAME>`: create a local user and grant sudo
  - `canfar_update`: update CANFAR scripts and CADC clients
```
