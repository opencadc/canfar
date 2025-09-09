# CASA container images

Notes about CASA container images available in Desktop sessions and compatibility considerations.

- Container images may differ by CASA major/minor version.
- Some CASA tasks rely on external system libraries; these are usually bundled in the container but check the release notes if you see missing symbols.

If you need GPU acceleration or special libraries, consult the container documentation for appropriate tags and runtime flags.

## Astroquery / astropy

The `astroquery` tool is installed on newer CASA containers (6.4.4-6.6.3). To use astroquery from the CASA Python:

```py
from astroquery.simbad import Simbad
result_table = Simbad.query_object("m1")
result_table.pprint()
```

## Analysis Utilities

The `analysisUtils` package is pre-installed on many CASA containers. You may need to run `import analysisUtils as au` to load it.

## ADMIT

ADMIT (ALMA Data Mining Tool) is available on some CASA containers (typically CASA >= 4.5); newer containers may exclude it.

## Known Container Notes

- Firefox is available on some CASA versions for minimal web-browser interaction.

## Example: restarting CASA (known issue workaround)

```sh
casa
exit
casa
```

## Example: run CASA with MPI and Xvfb (non-interactive)

```sh
xvfb-run -a mpicasa casa --nologger --nogui -agg -c casa_script.py
```
