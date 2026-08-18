# Software repositories (CVMFS)

[CVMFS](https://cvmfs.readthedocs.io/en/stable/) is a read-only, on-demand
filesystem for distributing large, versioned software trees. A Science
Platform deployment may mount one or more CVMFS repositories in Sessions. The
available repositories and software are deployment data; a missing path is not
an instruction to install a CVMFS client yourself.

CVMFS is for shared software and reference data. Keep notebooks, source code,
intermediate files, and research products in writable [Science Platform
storage](storage/index.md), not under `/cvmfs`.

## Check the repository

If your Session includes the Alliance software tree, the common path is:

```bash
ls /cvmfs/soft.computecanada.ca
source /cvmfs/soft.computecanada.ca/config/profile/bash.sh
module avail
```

Only run the `source` command when that path exists. The module list and
version names change as maintainers publish new software. Check the
[Alliance CVMFS](https://docs.alliancecan.ca/wiki/Accessing_CVMFS) and
[available software](https://docs.alliancecan.ca/wiki/Available_software)
guides for the current repository contents.

For a documented module, load it and record the module name and version with
the workflow:

```bash
module load python/3.10
python --version
module list
```

Module changes apply to the current process and Session. Put stable, required
dependencies in a versioned Container Image or environment rather than
depending on an unrecorded interactive shell.

## Trade-offs

- The first access can be slower while metadata and files are fetched.
- The filesystem is read-only; use `/arc` or `/scratch` for writable paths.
- A repository that is mounted on one server or Session Kind may not be
  mounted on another.
- A software version published in CVMFS is not automatically installed in a
  Container Image.

If a required repository is absent, ask the platform operator which supported
image or software distribution to use. Do not modify `/cvmfs` or rely on a
private node-local cache for reproducibility.

## Related guides

- [Container Images](containers/index.md)
- [Best practices](best-practices.md)
- [Storage](storage/index.md)
- [Alliance Using modules](https://docs.alliancecan.ca/wiki/Using_modules)
