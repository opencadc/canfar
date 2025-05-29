# Using VOS Tools for Data Transfer

VOS Tools provide the most efficient command-line method for transferring files between
your local computer and CANFAR's storage systems. These tools work with both the Science
Platform storage (ARC) and CANFAR's long-term archive (VOSpace).

## What are VOS Tools?

VOS Tools are command-line utilities that provide:
- **Fast, reliable transfers** with automatic retry and resumption
- **Directory synchronization** for keeping datasets current
- **Unified interface** for both ARC and VOSpace storage
- **Integration with scripts** for automated workflows

## Installation

Install VOS Tools on your personal computer following the instructions at:
[CANFAR Storage Documentation](https://www.canfar.net/en/docs/storage/)

Look for the section titled *"The vos Python module and command line client"*.

## Authentication

Before using VOS Tools, authenticate with CADC (Canadian Astronomy Data Centre) to obtain
a security certificate:

    cadc-get-cert -u [username]

**What this does**: 
- Creates an encrypted certificate file at `~/.ssl/cadcproxy.pem`
- Enables secure, authenticated access to CANFAR storage
- Certificate expires after 10 days (renewable)

**If you see an error**: `ERROR:: Expired cert. Update by running cadc-get-cert`
Simply re-run the command above to refresh your certificate.

## Common Commands and Examples

Here are some common `vostools` commands with examples. Remember to replace `[username]` with your actual CANFAR username and `[project_code]` with your project identifier.

### `vcp` (Copy Files)

The `vcp` command is used to copy files and directories.

* **Copy a local file to your ARC home directory:**

        vcp local_file.txt arc:home/[username]/

* **Copy a local file to a project directory in ARC:**

        vcp my_data.fits arc:projects/[project_code]/data/

* **Copy a file from ARC to your current local directory:**

        vcp arc:projects/[project_code]/results/plot.png ./

* **Copy an entire local directory recursively to ARC:**

        vcp -r local_directory/ arc:projects/[project_code]/analysis/

* **Copy an entire directory from ARC recursively to a local directory:**

        vcp -r arc:projects/[project_code]/raw_data/ ./my_local_raw_data/

* **Copy a file from your local machine to VOSpace:**

        vcp important_dataset.tar.gz vos:[username]/archive/

* **Copy a file from VOSpace to your local machine:**

        vcp vos:[username]/archive/important_dataset.tar.gz ./

* **Copy files between ARC and VOSpace (run from a CANFAR Science Platform terminal):**

  * ARC to VOSpace:

        vcp arc:projects/[project_code]/final_product.fits vos:[username]/release/

  * VOSpace to ARC:

        vcp vos:[username]/shared/calibration_file.dat arc:projects/[project_code]/calibrations/

    !!! note
        Direct transfers between ARC and VOSpace must be initiated from a terminal session within the CANFAR Science Platform.

### `vls` (List Files)

The `vls` command lists files and directories.

* **List files in your ARC home directory:**

        vls arc:home/[username]/

* **List files in an ARC project directory:**

        vls arc:projects/[project_code]/data/

* **List files in your VOSpace root:**

        vls vos:[username]/

* **List files in a specific VOSpace directory with more details (long listing):**

        vls -l vos:[username]/my_data_archive/

### `vmkdir` (Make Directory)

The `vmkdir` command creates new directories.

* **Create a new directory in your ARC home:**

        vmkdir arc:home/[username]/new_folder

* **Create a new directory within an ARC project:**

        vmkdir arc:projects/[project_code]/processed_images

* **Create a new directory in VOSpace:**

        vmkdir vos:[username]/my_simulations

### `vrm` (Remove Files/Directories)

The `vrm` command removes files or directories. Use with caution!

* **Remove a file from ARC:**

        vrm arc:home/[username]/old_file.txt

* **Remove a directory and its contents recursively from VOSpace (use with extreme caution!):**

        vrm -r vos:[username]/temporary_outputs/

### `vsync` (Synchronize Directories)

The `vsync` command synchronizes the content of two directories. This is useful for keeping a local directory and a remote VOSpace/ARC directory in sync.

* **Synchronize a local directory to an ARC project directory (uploads changes):**

        vsync ./local_analysis_files/ arc:projects/[project_code]/analysis_files/

* **Synchronize an ARC project directory to a local directory (downloads changes):**

        vsync arc:projects/[project_code]/results/ ./local_results_backup/

* **Synchronize a local directory to VOSpace:**

        vsync ./my_important_docs/ vos:[username]/documents_backup/

    !!! tip
        `vsync` can be very powerful. Consider using the `--dry-run` option first to see what changes would be made without actually performing them:
        `vsync --dry-run ./local_analysis_files/ arc:projects/[project_code]/analysis_files/`

### Other Useful Commands

* **`vattrib`**: View or modify attributes of a VOSpace node (e.g., permissions, group). This is more advanced.
* **`vfind`**: Search for files in VOSpace.

## File Paths and Structure

You may have noticed that the base directory structure differs slightly between VOSpace and the Science Portal (ARC):

* **ARC (Science Portal):** Typically starts with `arc:home/[username]/` for your home directory or `arc:projects/[project_code]/` for project spaces.
* **VOSpace:** Typically starts with `vos:[username]/`.

More information about VOS Tools can be found at:
[CANFAR Storage Documentation](https://www.canfar.net/en/docs/storage/)
