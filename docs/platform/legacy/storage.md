# VOSpace: CANFAR Storage System

!!! abstract "🎯 What You'll Learn"
    - What VOSpace is and why it matters for CANFAR users  
    - When to use VOSpace for data staging, storage, and sharing  
    - Requirements for accessing VOSpace (accounts and tools)  
    - Available access methods: web, CLI, Python `vos`, and `vofs` filesystem  
    - Best practices for storing and managing data in VOSpace  

VOSpace is the CANFAR storage system, an implementation of the Virtual Observatory specification.  
It provides long-term, secure, and collaborative storage for astronomy data.  
VOSpace is designed to integrate with CANFAR’s processing and workflows, making it the central hub for data preparation, analysis, and sharing.  

---

### Why use VOSpace
- **Reliable and secure**: Files are mirrored across four physical locations, protecting against disk failures.  
- **Long-term storage**: Intended for permanent or semi-permanent storage of astronomical data.  
- **Collaboration**: Enables data sharing between members of a project or research team.  

*VOSpace is especially useful when working with large datasets that must remain accessible and safe throughout a project lifecycle.*  

---

### When to use
- **Staging input data**: If your data are not already in a CADC archive, you can upload them to VOSpace for faster access during processing.  
- **Storing results**: Keep outputs from the CANFAR processing system in a central, backed-up location.  
- **Sharing data**: Exchange datasets with collaborators in a controlled and efficient way.  

*Think of VOSpace as your workspace “hub”: data comes in, gets processed, and results can be distributed or archived.*  

---

### Requirements
- **CADC account**: Access requires registration for a valid CADC account.  
- **Access methods**:  
  - **Web interface**: Easy to use, interactive, and familiar for browsing or uploading small datasets.  
  - **Python tools / CLI**: The `vos` module and command-line clients allow scripted and automated access.  
  - **Filesystem mount (vofs)**: FUSE-based view that works like a local folder. Convenient for browsing, but not recommended for heavy processing.  

*Choose the access method that best fits your workflow: web for simple interaction, CLI/`vos` for automated tasks, and `vofs` only for lightweight exploration.*  


[Open Web Storage :material-arrow-right:](https://www.canfar.net/storage/vault/list){: .md-button .md-button--primary }

Access requires a CADC account.

!!! tip "Related"
    - Python client & CLI examples are below.
    - [Publications/DOIs](publication.md).

## The `vos` CLI {#vos-cli}
Use the `vos` command-line client for scripts and terminals.

### Installation {#install}
- Python ≥ 3.7

```bash title="Install vos"
pip install -U vos
# or per-user
pip install --user -U vos
# ensure PATH includes user base
export PATH="${HOME}/.local/bin:${PATH}"
```

### Common commands (recommended) {#common-commands}
Replace `VOSPACE` with your space name (often your username; projects may have project spaces).

```bash
# list the root of the entire VOSpace
vls vos:

# copy a local file to the VOSPACE root
vcp "${HOME}/bar" "vos:[VOSPACE]"

# wildcards
vcp "vos:[VOSPACE]/foo/*.txt" .

# FITS cutout (pixels)
vcp "vos:[VOSPACE]/image.fits[1:100,1:100]" .

# or by coordinates (example)
vcp "vos:[VOSPACE]/image.fits(10.25,10.25,0.1)" .

# headers only
vcp --head "vos:[VOSPACE]/image.fits" .

# inspect headers
vcat --head "vos:[VOSPACE]/image.fits"

# remove an entry
vrm "vos:[VOSPACE]/foo"

# create a container (directory)
vmkdir "vos:[VOSPACE]/bar"

# move/rename
vmv "vos:[VOSPACE]/bar" "vos:[VOSPACE]/foo/"
vmv "vos:[VOSPACE]/foo/bar" "vos:[VOSPACE]/foo/bar2"

# group write permission
vchmod g+w "vos:[VOSPACE]/foo/bar.txt" 'GROUP1, GROUP2, GROUP3'

```

More help:

```bash
vls --help
pydoc vos.commands
```

### Python API {#python-api}
```python
from vos import Client

client = Client()
listing = client.listdir('vos:MyVOSpace')
client.copy('vos:MyVOSpace/Filename', '/local/filename')
```

## VOSpace FUSE filesystem (`vofs`) {#vofs}
Mount VOSpace as a remote filesystem via FUSE.

!!! warning "Performance"
    `vofs` is **not recommended** for batch or IO-heavy pipelines; it’s best for light interactive browsing.

### Install `vofs` {#vofs-install}
After installing `vos`, install `vofs`:

```bash
pip install -U vofs
# or per-user
pip install --user -U vofs
export PATH="${HOME}/.local/bin:${PATH}"
```

#### FUSE prerequisites {#fuse}
**Linux**

```bash
# some distros require FUSE and devel packages
sudo yum install -y fuse fuse-devel || true
# add your user to the fuse group (re-login required)
sudo /usr/sbin/usermod -a -G fuse "$(whoami)"
```

**macOS**

- Install **macFUSE**. If you hit a `libfuse.dylib` error with `mountvofs`, set:

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/usr/local/lib
```

#### Usage {#vofs-usage}
```bash
# mount all accessible VOSpaces
mountvofs

# inspect mount point
ls /tmp/vospace

# unmount
fusermount -u /tmp/vospace   # Linux
umount /tmp/vospace          # macOS

# mount a specific VOSpace
mountvofs --vospace vos:USER --mountpoint /path/to/a/directory
```

`mountvofs` creates a local cache (default 50 GiB, default `${HOME}/vos:USER`). It refreshes when the remote is newer; on close, writes are pushed back. Many science tools write infrequently and perform well; typical editors write temp files often and may degrade performance.

For options:

```bash
mountvofs --help
```

## Certificates (X509) {#certificates}
The CLI requires a valid certificate. CADC issues a long-lived certificate on account creation; batch uses short-lived **proxy certificates**.

```bash
cadc-get-cert -u <USERNAME>
```

### Using vos with batch VMs {#cert-batch}
Proxy certificates are injected automatically into batch workers at submission time. If not, alternatives:

**More secure (recommended)**

```bash
# on batch.canfar.net, obtain a proxy
cadc-get-cert -u <USERNAME>
# copy it to your submission directory
cp ${HOME}/.ssl/cadcproxy.pem .
```

Add to your submission file:

```text
should_transfer_files = YES
transfer_input_files = cadcproxy.pem
```

At the top of the job script:

```bash
mv cadcproxy.pem ${HOME}/.ssl/
```

**Less secure (not recommended)**
Run `cadc-get-cert` at job start. To avoid password prompts, create a `~/.netrc`:

```text
machine www.canfar.net login <USERNAME> password <PASSWORD>
```

```bash
chmod 600 ~/.netrc
```