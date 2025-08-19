# Cloud Services Overview

All the cloud services used by CANFAR are the Digital Research Alliance Canada (DRAC) OpenStack offerings. We strongly encourage the user to refer to the Digital Research Alliance Canada cloud documentation for reference.

The Digital Research Alliance Canada allocation resources are currently shared between all CANFAR users. Currently the main difference between the Digital Research Alliance Canada cloud and the CANFAR access are the following:

- Access to the cloud portals are with the CADC <span style="color: blue;">[username]</span> and password, not the Digital Research Alliance Canada
- The access is with [arbutus-canfar](https://arbutus-canfar.cloud.computecanada.ca/) instead of [arbutus](https://arbutus.cloud.computecanada.ca/)
- CANFAR will give reasonable resources for interactive analysis and very large for batch processing on the clouds.

## Registration and Resource Allocation

A CADC account (register) is required to access the cloud servicƒes.

Once registered, send an email to CANFAR support and include:

- A CADC account name
- A rough amount of required resources (storage capacity and processing capabilities), and if batch processing is needed
- A few sentences describing what you want to do.

The request will be reviewed and you will be contacted by the CANFAR team which will also take care of the registration to Digital Research Alliance Canada infrastructure.

Below we include a tutorial describing a typical workflow using the OpenStack Cloud Services and batch with CANFAR.

## Batch Tutorial

### Introduction

This guide will demonstrate how to create a basic source detection pipeline operating on CFHT Megacam images within the CANFAR Virtual Machine (VM), with fast access to the CADC archive and storage. It will go over the following steps:

- Create, configure, and interact with Digital Research Alliance Canada OpenStack cloud, and CANFAR VMs
- Access CADC VOSpace storage
- Launch jobs running the pipeline installed on the VM with the CANFAR batch system

This guide is mostly geared to do batch data processing. If only access to the Digital Research Alliance Canada cloud to build persistent (non-batch) VMs, we suggest this guide, which also applies to CANFAR.

In this guide:

- <span style="color:#4DA6FF">[username]</span> is the CADC username
- <span style="color:#4DA6FF">[VOSpace]</span> is the short VOSpace name
- <span style="color:#4DA6FF">[project]</span> is the OpenStack project name

### Create a Virtual Machine

To access and manage a VM with OpenStack, we suggest using the web dashboard at Digital Research Alliance Canada.

1. [Log into the dashboard](https://arbutus-canfar.cloud.computecanada.ca/). Provide a CADC <span style="color:#4DA6FF">[username]</span> and <span style="color:#4DA6FF">[password]</span>.
2. Each CANFAR resource allocation corresponds to an OpenStack `[project]`. A user may be a member of multiple projects, and a project usually has multiple users. A pull-down menu near the top-left allows a selection between the different projects.

To create a VM we will follow [these instructions](https://docs.alliancecan.ca/wiki/Creating_a_Linux_VM), summarized in the 4 next sections.

#### Import an SSH public key

Access to VMs is facilitated by [SSH key pairs](https://docs.alliancecan.ca/wiki/SSH_Keys) rather than less secure user name / password. A private key resides on the local computer, and the public key is copied to all remote machines.

1. If no SSH key pair exists on the local machine, run the <span style="color:#4DA6FF">ssh-keygen</span> command from a terminal on the local machine to generate one, or follow this [documentation](https://docs.alliancecan.ca/wiki/SSH_Keys).
2. On the dashboard, click on **Compute**, switch to the **Key Pairs** tab and click on the **Import Key Pair** button (top-right).
3. Choose a meaningful name for the key, and then copy and paste the contents of the public key. The default location is at <span style="color:#4DA6FF">`$HOME/.ssh/id_rsa.pub`</span> on the local machine, into the Public Key window.

#### Allocate a public IP address

To connect to the VM remotely, the VM needs a public IP address.

1. Click on the **Floating IPs** tab part of **Network**. If there are no IPs listed, click on the **Allocate IP to Project** button at the top-right.
2. Each project will typically be given one public IP. If all IPs were already allocated, this button will read "Quota Exceeded".

#### Launch a VM instance

We will now launch a VM. A VM comes with an operating system, and we support two Linux distributions: Ubuntu LTS and RedHat Enterprise Linux clone (Rocky Linux). For this tutorial, we will select Ubuntu 20.04 based VM, which contains a few CANFAR specific pre-installed packages.

Follow these steps to access and launch those pre-built VMs:

1. Switch to the **Compute** tab, then on **Instances**, click on the **Launch Instance** button on the right.
2. Fill up the form of the VM:
   - **Details**: choose a meaningful Instance Name
   - **Source**: select Boot Source as an Instance Snapshot and choose **canfar-ubuntu-20.04**. This is especially important to choose an Image or Instance Snapshot for batch processing.
   - **Flavor**: the resources of the VM. <span style="color:#4DA6FF">c2-7.5gb-30</span> provides 2 CPU (equivalent), 7.5GB RAM, and a 31 GB ephemeral disk that will be used as scratch space. The flavours starting with **p** are persistent VMs, and do not have scratch space.
   - **Key Pair**: ensure the proper SSH public key is selected
3. Finally, click the **Launch** button.

#### Connect to the VM instance

After launching the VM, the interface shows the Instances window. Wait for the power state of the VM instance to say **Running**. Before being able to ssh to the instance, attach the public IP address to it.

1. Select **Associate Floating IP** from the pull-down menu on the right of Create Snapshot button.
2. Select an allocated IP address

The SSH public key will be injected into the VM instance under a [generic](https://docs.alliancecan.ca/wiki/Cloud_Quick_Start#Connecting_to_your_VM_with_SSH) account. The default username depends on the initial selected VM image at launch time: an Ubuntu-based VM will have a default **ubuntu** user. A Rocky-Linux (equivalent RedHat Enterprise) based VM will have <span style="color:#4DA6FF">rocky</span> as the default username. This user is not related to the CADC user.

Try to access the running VM instance:

```bash
ssh ubuntu@[floating ip]
```

Once connected, create a user on the VM with a CADC <span style="color:#4DA6FF">[username]</span>. Create a user with the CADC <span style="color:#4DA6FF">[username]</span>, with the following command:

```bash
sudo canfar_create_user [username]
```

Logout from the VM and ssh back in with <span style="color:#4DA6FF">ssh [username]@[floating ip]</span>.

### Install software on the VM

The VM operating system has only a minimal set of packages. For this example, we will add two packages:

- The [Source EXtractor](https://sextractor.readthedocs.io/) software, to detect astronomical sources in FITS images, resulting in catalogues of stars and galaxies.
- The [funpack](https://heasarc.gsfc.nasa.gov/fitsio/fpack/) software, a file decompressor. We also need to read FITS images. Most FITS images from CADC come Rice-compressed with an <span style="color:#4DA6FF">fz</span> extension. <span style="color:#4DA6FF">SExtractor</span> only reads uncompressed images, so we also need the <span style="color:#4DA6FF">funpack</span> utility to uncompress the incoming data. In Debian/Ubuntu, the <span style="color:#4DA6FF">funpack</span> executable is included in the package <span style="color:#4DA6FF">libcfitsio-bin</span>.

Let's install them system wide since they are available in Ubuntu software repository, after a fresh update:

```bash
sudo apt update -y
sudo apt install -y source-extractor libcfitsio-bin
```

### Test the Software on the VM instance

We are now ready to do our basic pipeline. Let's download a FITS image to the scratch space. When we instantiated the VM, we selected a flavour with an ephemeral disk. The disk was automatically mounted on <span style="color:#4DA6FF">`/mnt`</span>. We want to access the ephemeral disk as a non-root user. This simple command will create a scratch directory on <span style="color:#4DA6FF">`/mnt/scratch`</span>, and give the proper permissions:

```bash
sudo canfar_setup_scratch
```

**Important notes concerning the scratch space:**

- The `canfar_setup_scratch` command needs to be run every time a new VM instance is launched
- When the VM runs in batch mode, the scratch directory will be setup automatically in a different directory for each batch job, which is **NOT** <span style="color:#4DA6FF">`/mnt/scratch`</span> (see below).

Next, enter the scratch directory, download an astronomical image from CADC of the CFHT Megaprime there, and detect the sources with our newly installed software. Here we take the default configuration of SExtractor and decide to only output the positions and magnitudes of the detected sources.

```bash
cd /mnt/scratch
cp /usr/share/source-extractor/default* .
echo 'NUMBER
MAG_AUTO
X_IMAGE
Y_IMAGE' > default.param
cadcget cadc:CFHT/1056213p.fits.fz
funpack -D 1056213p.fits.fz
source-extractor 1056213p.fits -CATALOG_NAME 1056213p.cat
```

The image **1056213p.fits** is a Multi-Extension FITS file with 36 extensions, each containing data from one CCD from the CFHT Megacam camera. The `cadcget` command downloads the FITS image from CADC and stores it on the current directory and is already installed on the VM (**cadcdata** python module). The resulting catalogue of detected sources is stored under **1056213p.cat**.

### Store results on the CANFAR VOSpace

All data stored on ephemeral disk will be wiped out when the VM instance terminates. We only want to store the output catalogue **1056213p.cat** at a persistent, externally accessible location. We will use the CADC VOSpace for this purpose. To store files on the VOSpace from a command line, we will use the CADC python VOSpace client (**vos** python module) which is already installed on the VM.

For an automated procedure to access the VOSpace, a proxy authorization must be present on the VM. One way to accomplish this is with a <span style="color:#4DA6FF">`.netrc`</span> file that contains the CADC user name and password, and the command <span style="color:#4DA6FF">cadc-get-cert</span> can obtain an X509 Proxy Certificate using that username/password combination without any further user interaction. The commands below will create the file and get a proxy certificate. A proxy certificate is by default valid 10 days.

```bash
cadc_dotnetrc # only needed once to create the file
cadc-get-cert -n # should generate a new proxy certificate
```

During batch, a new proxy certificate will be created at submission and later injected into all the VM workers. Let's check that the VOSpace client works by uploading the output source catalogue:

```bash
vcp 1056213p.cat vos:[VOSpace]
```

Verify that the file is properly uploaded by pointing the browser to the VOSpace browser interface.

### Snapshot (save) the VM Instance

Now we want to save the VM with the new installed software. Return to the OpenStack dashboard on the browser.

Save the state of the VM by navigating to the **Instances** window of the dashboard and click on the **Create Snapshot** button to the right of the VM instance's name. After selecting a meaningful name for the snapshot of the VM instance, e.g., **image-reduction-2023-08-21**, click the **Create Snapshot** button. The VM instance will eventually be saved and the snapshot should be listed in the **VM Images** window. Next time, a new instance of that VM image snapshot can be launched.

**Note:** while the system is taking a snapshot of the VM, avoid doing anything on the VM instance.

**IMPORTANT:** if no snapshot of the VM, all work on the VM will be lost when the VM instance is deleted. Volume-based VMs do not need snapshots and will persist the files directly on a persistent disk, but Volume-based VM cannot be used for batch processing.

If batch processing is needed, carry on.

### Make a script to automate the pipeline

Batch jobs in CANFAR are scheduled and launched with the [HTCondor](http://www.htcondor.org/) software. The [cloud scheduler](http://www.cloudscheduler.org/) will launch the necessary VM instances, to process the jobs on demand, and HTCondor will launch the jobs on the launched VMs (workers).

Now we want to automate the whole procedure as a batch script. SSH into the CANFAR batch cluster:

```bash
ssh [username]@batch.canfar.net
```

We need to recreate and automate the same procedure done interactively. We can simply put all the necessary commands into a pipeline script. Paste the following commands into one BASH script named <span style="color:#4DA6FF">`~/do_catalogue.bash`</span>:

```bash
#!/bin/bash
id=$1
cadcget cadc:CFHT/${id}.fits.fz
funpack -D ${id}.fits.fz
cp /usr/share/source-extractor/default* .
echo 'NUMBER
MAG_AUTO
X_IMAGE
Y_IMAGE' > default.param
source-extractor ${id}.fits -CATALOG_NAME ${id}.cat
vcp ${id}.cat vos:[VOSpace]/
```

The script will repeat the same commands as before with one image observation ID as an argument:

- Download the compressed FITS file corresponding to the ID from CADC
- Uncompress the file
- Detect the sources
- Save the resulting catalogue of detected sources to the VOSpace.

Remember to substitute <span style="color:#4DA6FF">[VOSpace]</span> with its name within the code snippets.

### Write a job submission file

We now want to apply this pipeline to a few images. We need to write a submission file to tell the job scheduler to launch all necessary jobs, in this case one per Megacam image. We need to transfer the <span style="color:#4DA6FF">do_catalogue.bash</span> script to a worker VM. The worker VM will be an instance of the frozen snapshot VM image. For each given observation ID, a job will run on the worker. Let's take the following image IDs: **1056215p**, **1056216p**, **1056217p**, and **1056218p**. Paste the following text into a submission file with an editor on the batch login node:

```
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

Let's save the submission file as <span style="color:#4DA6FF">do_catalogue.sub</span>. Each job will execute with an output and an error file. At the end of each job, all the log files will be transferred to the directory on <span style="color:#4DA6FF">batch.canfar.net</span> where the job was submitted.

### Submit the batch jobs

We need two authorizations to run the batch jobs:

- To give the scheduler access to launch VM snapshot stored in the `[project]` space
- To give write access to `[VOSpace]` to store results

In the home directory on the batch host, there is one or more <span style="color:#4DA6FF">*-openrc.sh</span> file(s), corresponding to the OpenStack projects you belong to.

Source the OpenStack RC project file, and enter the CADC password. This sets environment variables used by OpenStack (only required once per batch host login session):

```bash
. [project]-openrc.sh
```

Now we can submit the jobs to the condor job pool with the following command:

```bash
canfar_submit do_catalogue.sub catalogue-software-2023-08-21 c2-7.5gb-30
```

Where:

- <span style="color:#4DA6FF">~/do_catalogue.bash</span>: is the path of the submission file
- <span style="color:#4DA6FF">~/do_catalogue.bash</span>: is the name of the snapshot VM used to install all the software
- <span style="color:#4DA6FF">c2-7.5gb-30</span>: is the resource flavour for the VM(s) that will execute the jobs. Resources are visible through the dashboard when launching an instance, or using the command line `openstack flavor list`.

After submission, we can check where the jobs stand in the queue:

```bash
condor_q
```

Monitoring the queue, we should see our jobs going from idle (**I**) to running (**R**). Once no more jobs are in the queue, we can check the logs and output files **105621.*** on the batch host, and check the VOSpace browser that all 4 of the generated catalogues were properly uploaded.

We can also check the status of the VMs and jobs running on the cloud summarizing all users:

```bash
condor_q -all
```

If access to the interactive VM instance is not needed for a while, terminate it from the OpenStack dashboard, by selecting the VM instance, clicking on **Delete Instances**.

## Extra: helpful CANFAR commands and VM maintenance

Once the VM is built, the responsibility is yours to maintain and update software. Running `sudo dnf update` or `sudo apt update` followed by a `sudo apt dist-upgrade` to apply the latest security updates from the Linux distributions is usually enough.

On the CANFAR pre-built VMs (**canfar-ubuntu-20.04** and **canfar-rocky-8**), there are a few scripts to help out with CANFAR related activities, all of them come with a `--help`:

- `cadc_cert -u [username]`: get a CADC proxy certificate by various methods to access CADC VOSpace (legacy script)
- `cadc_dotnetrc`: update / create a <span style="color:#4DA6FF">${HOME}/.netrc</span> file to ease out with CADC VOSpace access
- `canfar_setup_scratch`: simple script to authorize a scratch space when in interactive mode on <span style="color:#4DA6FF">/mnt/scratch</span>
- `canfar_create_user [user]`: create a user with a name `[user]` on the VM and propagate ssh public key, and give sudo access
- `canfar_update`: update all the CANFAR scripts and CADC clients on the VM with the latest versions.

All these commands reside on <span style="color:#4DA6FF">/usr/local/bin</span>, and can be found at the GitHub source.