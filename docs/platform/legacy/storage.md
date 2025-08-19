# Storage Management

## Introduction
VOSpace is the CANFAR storage system, an implementation of the Virtual Observatory Specification. It is intended to be used for storing the output of the CANFAR processing system and also for sharing files between members of a collaboration. If the data to be processed is not already on a CADC archive, it can be staged on a VOSpace for faster access. Files in VOSpace are also mirrored in four physical locations, so they are secure against disk failure, and designed for long term.

Access to VOSpace requires a CADC account (registration).

There are two ways to interact with VOSpace. The first is with your browser via the web user interface. The web interface is familiar for most people to use and interactive. To access a VOSpace in scripts, the Python-based `vos` module and command line clients are available. Some users might also find the VOSpace filesystem `vofs`, the FS view is based on FUSE and not recommended for serious data processing, but does provide a convenient interactive interface for exploring a repository.

[:material-database: Web Storage Interface ](https://www.canfar.net/storage/vault/list){: .md-button .md-button--primary }

## The vos Python module and command line client
The VOSpace can also be accessed via some commands on a terminal or a script. They are part of the `vos` command line client.

### Installation
1. Ensure Python is up-to-date (at least 3.7)
2. Install the vos module using pip:

```bash title="Install vos"
pip install -U vos

# or if you didn't use conda or a user install is required:
pip install --user -U vos

# You might also need to update your path:
export PATH="${HOME}/.local/bin:${PATH}"
```

### Using the client command line tools (recommended)
Try the following commands, substituting your CANFAR VOSpace in for VOSPACE (most CANFAR users have VOSpace that is the same name as their CANFAR user name. There are also project VOSpaces):
```bash
# lists the contents to the root directory of the entire VOSpace system
vls vos:

# copies the bar file from the local disk to the root node of VOSPACE
vcp ${HOME}/bar vos:VOSPACE

# wildcards also work
vcp vos:VOSPACE/foo/*.txt .

# FITS cutouts at the service side in pixels
vcp vos:VOSPACE/image.fits[1:100,1:100] .

# or coordinates
vcp vos:VOSPACE/image.fits(10.25,10.25,0.1) .

# copy just the headers of the FITS file
vcp --head vos:VOSPACE/image.fits .

# examine the headers of the FITS file
vcat --head vos:VOSPACE/image.fits

# remove the bar file from VOSPACE
vrm vos:VOSPACE/foo

# create a new container node (directory) called foo in VOSPACE
vmkdir vos:VOSPACE/bar

# move the file bar into the container node foo
vmv vos:VOSPACE/bar vos:VOSPACE/foo/

# change the name of file bar to bar2 in VOSPACE
vmv vos:VOSPACE/foo/bar vos:VOSPACE/foo/bar2

# provide group write permission on a VOSpace location
vchmod g+w vos:VOSPACE/foo/bar.txt 'GROUP1, GROUP2, GROUP3'
```

Details on these commands can be found via the <span style="color:#4DA6FF">--help option</font> , e.g. <span style="color:#4DA6FF">vls --help</font>. And if you want to see a more verbose output, try <span style="color:#4DA6FF">vls -v vos:VOSPACE.</font>

The following commands are defined: <span style="color:#4DA6FF">vcat vchmod vcp vln vlock vls vmkdir vmv vrm vrmdir vsync vtag</font>

Help on these commands can also be found using <span style="color:#4DA6FF">pydoc</font>

```bash
pydoc vos.comamnds
```
### Using the vos python module API
There is documentation built into the libary <span style="color:#4DA6FF">pydoc vos</font>. Here we provide a very basic example usage.
```bash
from vos import Client

directory_listing = Client().listdir('vos:MyVOSpace')
Client().copy('vos:MyVOSpace/Filename', '/local/filename')
```

## The VOSpace FUSE based file system
VOSpace can also be accessed as a remote filesystem using the vofs python module. This technique uses a FUSE layer between file-system actions and the VOSpace storage system. Using vofs makes your VOSpace appear like a regular filesystem.

__vofs is not recommended for batch processing or i/o heavy applications__

#### Installation
- Follow the instructions for installing vos. Then follow the instructions below.
- Install the vofs python module.

#### FUSE
**Linux**
- On some distros (RHEL 5, CentOS 5, Scientific Linux 5) you may need to add the fuse library:
```bash
sudo yum install fuse fuse-devel
```
- On all distros you will also need to add your account to the fuse group of users, to be allowed to make filesystem mounts work:
```bash
sudo /usr/sbin/usermod -a  -G fuse `whoami`
```
#### OS-X
- Install OSX-FUSE first (you will need to install this package in ‘MacFUSE Compatibility’ mode, there is a selection box for this during the install).

#### vofs
The <span style="color:#4DA6FF">vofs</font> python module is dtributed via [PyPi](https://pypi.org/project/vofs/).
```bash
pip install -U vofs
```
or user based
```bash
pip install --user -U vofs
# You might need to add the install area to your path
export PATH="${HOME}/.local/bin:${PATH}"
```
#### Usage
- Mount all available VOSpaces:
```bash
mountvofs
```
On some OS-X installations the mountvofs command will result in an error like ‘libfuse.dylib’ not found. Setting the environment variable <span style="color:#4DA6FF">DYLD_FALLBACK_LIBRARY_PATH</font> can help resolve this issue:
```bash
export DYLD_FALLBACK_LIBRARY_PATH=/usr/local/lib
```
Now looking in <span style="color:#4DA6FF">/tmp/vospace</font> you should see a listing of all available VOSpaces that you have read access.

- List the root of vospace
```bash
ls /tmp/vospace
```
- Unmount the VOSpace:
```bash
fusermount -u /tmp/vospace   # Linux
umount /tmp/vospace          # OS-X
```
- Mount a specific VOSpace:
```bash
mountvofs --vospace vos:USER --mountpoint /path/to/a/directory
```
The <span style="color:#4DA6FF">mountvofs</font> command creates a cache directory where local copies of files from the VOSpace are kept, as needed. If the cached version is older than the copy on VOSpace then a new version is pulled. You can specify the size of the cache (default is 50 GBytes) and the location (default is <span style="color:#4DA6FF">${HOME}/vos:USER</font>) on the command line.

When a file is opened in a mounted directory, mountvofs gets the remote copy from VOspace, if the local copy is out of date. When the file is written to disk and closed, the VOSpace file system puts the file back into VOspace. With most science software, these operations typically occur rarely and the illusion of a local disk is maintained. Most editors, however, tend to write temporary versions of a file frequently. In this case, the file is frequently written to VOspace. Performance may suffer in this case, or not even being compatible with the application.
- Options
There are many options that can help improve your vofs experience (in particular vofs is most useful in –readonly mode). To see all the possible options use the –help flag.
```bash
mountvofs --help
```
#### Retrieving CANFAR X509 certificates
To access a VOSpace, the command line client needs a certificate. These certificates are created when a CADC account is created, and a short-lived proxy of this certificate can be obtained. One easy way is with the cadc-get-cert command line, distributed with the cadcutils library that was automatically installed as part of the vos installation process above.
```bash
cadc-get-cert -u USER
```
#### Using vos with batch processing VM
In batch processing, the CADC proxy certificate will be transferred automatically to the batch VMs, ensuring the certificate is valid at submission time. If this does not happen, there are two approaches:
#### Secure but slightly complicated

- On the CANFAR batch submission host, `batch.canfar.net`, run the command  
  <span style="color:#4DA6FF">cadc-get-cert</span>:

    ```bash
    cadc-get-cert -u USER
    ```

- Copy the file `$HOME/.ssl/cadcproxy.pem` to the directory where you are submitting your jobs from:

    ```bash
    cp ${HOME}/.ssl/cadcproxy.pem .
    ```

- Add cadcproxy.pem to the list of files to transfer when the job executes (this is the done by adding these lines the submission file).

should_transfer_files = YES
transfer_input_files = cadcproxy.pem

- Add this line to the start of the batch script:

    ```bash
    mv cadcproxy.pem ${HOME}/.ssl/
    ```

#### Insecure but slightly less complicated
Use the cadc-get-cert script at the start of every job. To avoid cadc-get-cert from asking for a password, ensure there is a valid `$HOME/.netrc` file on the snapshotted VM, containing these lines:

```bash
machine www.canfar.net USER password PASSWORD
```

and do:
```bash
chmod 600 $HOME/.netrc
```

_WARNING_: this is not a fully secure solution
