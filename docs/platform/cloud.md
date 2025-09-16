# Legacy Cloud Platform (OpenStack VMs)

!!! warning "Legacy Platform"
    This documentation covers the legacy CANFAR cloud platform based on OpenStack virtual machines. For new users, we recommend the modern [CANFAR Science Platform](get-started.md) which provides container-based sessions, improved workflows, and better resource management.

!!! abstract "🎯 What You'll Learn"
    - How to access legacy CANFAR cloud services via Digital Research Alliance Canada (DRAC) OpenStack
    - Differences between DRAC OpenStack cloud and modern CANFAR platform access
    - VM management and batch processing workflows
    - Migration strategies to the modern platform

The legacy CANFAR cloud services are hosted on the Digital Research Alliance Canada (DRAC) OpenStack infrastructure. This platform provides traditional virtual machines for users who require persistent compute environments or have specific legacy workflow requirements.

## 🔄 Migration to Modern Platform

Before proceeding with OpenStack VMs, consider whether the [modern CANFAR Science Platform](index.md) meets your needs:

### Modern Platform Advantages

- **Container-based sessions**: Faster startup, better resource utilisation
- **Browser-native access**: No SSH or complex networking required
- **Automated resource management**: Dynamic scaling and optimised allocation
- **Integrated storage**: Seamless access to shared `/arc/`
- **Pre-configured environments**: Ready-to-use astronomy software stacks

### When to Use Legacy Platform

- **Persistent services**: Long-running applications that need to stay active
- **Custom system configurations**: Root access requirements
- **Legacy workflows**: Existing scripts and pipelines that require VMs
- **Old VM Batch processing**: Large-scale automated job processing which was installed on a VM

## 🔑 Access and Authentication

### Key Differences from DRAC Defaults

- **Credentials**: Sign in with **CADC Username/Password** (not a DRAC account)
- **Portal**: Use the [arbutus-canfar portal](https://arbutus-canfar.cloud.computecanada.ca/) (instead of [arbutus](https://arbutus.cloud.computecanada.ca/))
- **Resource policy**: Interactive analysis gets reasonable quotas; **batch processing** can scale to large footprints

### Registration & Allocation

A CADC account is required to access cloud services.

1. **Register a CADC account** (if you don't have one)
2. **Email CANFAR support** with:
    - Project Name
    - CADC Account Username
    - Estimated resources (storage, compute; whether you need batch)
    - A short description of your use case (2–3 sentences)

CANFAR will review and coordinate project/quotas on the DRAC side.

## 🖥️ Virtual Machine Management

### Creating and Configuring VMs

#### 1. Create a VM

Use the DRAC web dashboard:

1. Sign in to [Dashboard](https://arbutus-canfar.cloud.computecanada.ca/) with CADC username/password
2. Each CANFAR allocation maps to an OpenStack **Project**. Use the top-left project picker to switch if you belong to multiple
3. Follow DRAC's [Creating a Linux VM](https://docs.alliancecan.ca/wiki/Creating_a_Linux_VM) documentation

#### 2. Import an SSH Public Key

OpenStack prefers SSH key pairs over passwords:

- If you do not have a key pair, run `ssh-keygen` locally or follow DRAC's SSH Keys documentation
- In **Compute → Key Pairs**, click **Import Key Pair**
- Name the key and paste your public key (default path `~/.ssh/id_rsa.pub`)

#### 3. Allocate a Public IP

- Go to **Network → Floating IPs**
- If none is listed, click **Allocate IP to Project**
- Typically, each project has one public IP; if exhausted you'll see _Quota Exceeded_

#### 4. Launch an Instance

- In **Compute → Instances → Launch Instance**, choose:
  - **Source**: _canfar-ubuntu-20.04_ (important for batch compatibility)
  - **Flavor**: e.g., `c2-7.5gb-30` (2 vCPU / 7.5 GiB RAM / ~31 GiB ephemeral disk)
  - **Key Pair**: select your SSH key
- Click **Launch**

#### 5. Connect to the Instance

After status becomes **Running**:

1. **Associate floating IP** (menu → **Associate Floating IP**)
2. **SSH to the instance**:

    ```bash
    ssh ubuntu@[floating_ip]
    ```

3. **Create a local user** matching your CADC account:

    ```bash
    sudo canfar_create_user [user]
    ```

## 🔧 VM Configuration and Tools

### Pre-built VM Helpers

The `canfar-ubuntu-20.04` and `canfar-rocky-8` images include helpful tools:

```bash
# Obtain a CADC proxy (legacy helper)
cadc_cert -u [user]

# Create/update ~/.netrc for CADC services
cadc_dotnetrc

# Set up /mnt/scratch for temporary storage
canfar_setup_scratch

# Create a local user and grant sudo access
canfar_create_user [user]

# Update CANFAR scripts and CADC clients
canfar_update
```

### System Maintenance

Keep your VM updated and secure:

```bash
# Ubuntu/Debian systems
sudo apt update && sudo apt dist-upgrade

# Rocky/CentOS systems
sudo dnf update
```

## 🚀 Batch Processing Workflow

### Setting Up Batch Processing

This tutorial demonstrates building a basic **source detection** pipeline for CFHT MegaCam images on a CANFAR VM with fast access to the CADC archive and VOSpace.

!!! note "You will learn to"
    - Create/manage VMs on DRAC OpenStack / CANFAR
    - Access CADC VOSpace from VMs
    - Submit batch jobs that run your pipeline

### 1. Create a VM

Use the DRAC web dashboard.

1. Sign in to [Dashboard](https://arbutus-canfar.cloud.computecanada.ca/) with CADC `[user]`/password.
2. Each CANFAR allocation maps to an OpenStack **`[project]`**. Use the top-left project picker to switch if you belong to multiple.

Follow DRAC's [Creating a Linux VM](https://docs.alliancecan.ca/wiki/Creating_a_Linux_VM). Summary below.

### 2. Import an SSH Public Key

OpenStack prefers SSH key pairs over passwords.

- If you do not have a key pair, run `ssh-keygen` locally or follow DRAC's SSH Keys documentation.
- In **Compute → Key Pairs**, click **Import Key Pair**.
- Name the key and paste your public key (default path `~/.ssh/id_rsa.pub`).

### 3. Allocate a Public IP

- Go to **Network → Floating IPs**.
- If none is listed, click **Allocate IP to Project**.
- Typically, each project has one public IP; if exhausted you'll see _Quota Exceeded_.

### 4. Launch an Instance

- In **Compute → Instances → Launch Instance**, choose:
  - **Source**: _canfar-ubuntu-20.04_ (important for batch)
  - **Flavor**: e.g., `c2-7.5gb-30` (2 vCPU / 7.5 GiB RAM / ~31 GiB ephemeral disk)
  - **Key Pair**: select your SSH key
- Click **Launch**.

### 5. Connect to the Instance

After status becomes **Running**, first **associate** the floating IP (menu → **Associate Floating IP**), then SSH:

```bash
ssh ubuntu@[floating_ip]
```

Create a local user matching your CADC account (for audit/minimal access):

```bash
sudo canfar_create_user [user]
logout
ssh [user]@[floating_ip]
```

!!! note "Default image users"
    - Ubuntu images: `ubuntu`
    - Rocky Linux images: `rocky`

### Install software

The base VM image comes with only a minimal set of packages.  
For this example, we need to install two additional tools:

- [Source Extractor](https://sextractor.readthedocs.io/) (source detection): software used to detect astronomical sources in FITS images, producing catalogues of stars and galaxies.
- [funpack](https://heasarc.gsfc.nasa.gov/fitsio/fpack/) (FITS decompressor; Ubuntu package `libcfitsio-bin`): a decompression utility for FITS images. Most FITS images provided by CADC are Rice-compressed and stored with an `.fz` extension. Since Source Extractor only accepts uncompressed images, we will use `funpack` to uncompress them. The `funpack` executable is distributed as part of the `libcfitsio-bin` package in Debian/Ubuntu.

Because both tools are available from the Ubuntu software repository, we can install them system-wide after updating the package index:

```bash title="Install packages"
sudo apt update -y
sudo apt install -y source-extractor libcfitsio-bin
```

### Test on the VM

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

### Persist results to VOSpace

Ephemeral storage is wiped when the VM terminates. Upload the output `1056213p.cat` to **VOSpace** (the VM includes the `vos` client).

Obtain a proxy certificate for automated access:

```bash
cadc_dotnetrc      # one-time helper to create ~/.netrc
cadc-get-cert -n   # generate an X509 proxy (default 10 days)
```

```bash
vcp 1056213p.cat vos:[project]/
```

!!! danger "Credential hygiene"
    `.netrc` stores credentials in plaintext. Use only on controlled hosts and restrict permissions: `chmod 600 ~/.netrc`.

### Snapshot the instance

In the **Instances** view, click **Create Snapshot** (e.g., name it `image-reduction-2023-08-21`).

!!! warning
    Avoid writes on the VM while a snapshot is being created.

Without a snapshot, **ephemeral** data is lost when the instance is deleted. **Volume-backed** VMs persist data but are **not suitable for batch**.

### Automate as a batch script

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
vcp "${id}.cat" "vos:[project]/"
```

### Write a submission file

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

### Submit jobs

Two authorizations are needed:

- Access to snapshots in `[project]`
- Write access to `vos:[project]`

On the batch login node `batch.canfar.net`:

```bash
ssh [user]@batch.canfar.net
. [project]-openrc.sh     # set OpenStack env (once per session)
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

## Extras: Helpful Commands & VM Maintenance

**Keep the OS updated:**

```bash
# Ubuntu/Debian systems
sudo apt update && sudo apt dist-upgrade

# Rocky/CentOS systems  
sudo dnf update
```

**Prebuilt VM helpers** (`canfar-ubuntu-20.04` / `canfar-rocky-8`):

- `cadc_cert -u [user]`: obtain a CADC proxy (legacy helper)
- `cadc_dotnetrc`: create/update `~/.netrc`
- `canfar_setup_scratch`: set up `/mnt/scratch`
- `canfar_create_user [user]`: create a local user and grant sudo
- `canfar_update`: update CANFAR scripts and CADC clients

### Migration Strategies

#### Option 1: Containerise Your Workflow

Convert your VM-based pipeline to containers:

1. **Create a Dockerfile** based on your VM configuration
2. **Test the container** on the modern platform
3. **Submit container-based jobs** instead of VM jobs

#### Option 2: Hybrid Approach

Use both platforms as appropriate:

- **Development**: Modern platform for interactive analysis
- **Production**: VM batch jobs for large-scale processing
- **Data sharing**: Common storage accessible from both

#### Option 3: Gradual Migration

Migrate components incrementally:

1. **Start with interactive work** on the modern platform
2. **Keep batch processing** on VMs initially
3. **Gradually containerise** pipeline components
4. **Complete migration** when ready

## 🔗 Migration Resources

### Modern Platform Documentation

- **[CANFAR Science Platform →](index.md)**: Overview of modern container-based platform
- **[Interactive Sessions →](sessions/index.md)**: Browser-based computing environments
- **[Container Usage →](containers/index.md)**: Working with pre-built and custom containers
- **[Batch Jobs →](sessions/batch.md)**: Modern batch processing workflows

### Support and Migration Assistance

- **Email**: [support@canfar.net](mailto:support@canfar.net) for migration planning
- **Documentation**: Platform comparison and migration guides
- **Consultation**: Schedule time to discuss your specific use case

## 📋 Platform Comparison

| Feature | Legacy OpenStack VMs | Modern CANFAR Platform |
|---------|---------------------|----------------------|
| **Access Method** | SSH, web dashboard | Browser-based interface |
| **Startup Time** | 5-10 minutes | 30-60 seconds |
| **Resource Management** | Manual VM sizing | Dynamic allocation |
| **Software Installation** | Manual setup required | Pre-configured containers |
| **Collaboration** | Shared VM access | Session sharing, unified storage |
| **Maintenance** | User responsibility | Platform managed |
| **Best For** | Persistent services, custom configs | Interactive analysis, quick workflows |

!!! tip "Choosing the Right Platform"
    - **New users**: Start with the [modern CANFAR platform](index.md)
    - **Existing VM users**: Consider migration for better efficiency
    - **Persistent services**: Continue using VMs where appropriate
    - **Hybrid workflows**: Use both platforms as needed
