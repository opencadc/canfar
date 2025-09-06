# CASA Container Reference

This page provides specific information about using CASA containers on CANFAR, including available tools, known issues, and troubleshooting tips.

!!! info "Integration Note"
    This is a technical reference for CASA-specific details. For comprehensive radio astronomy workflows, see the main [Radio Astronomy Guide](../guides/radio-astronomy/index.md).

## Available CASA Versions

CANFAR provides multiple CASA versions to support different workflows and compatibility requirements:

- **CASA 6.5** (recommended): Latest stable release with Python 3 support
- **CASA 6.4**: Previous stable version for compatibility
- **CASA Pipeline**: Automated calibration and imaging pipelines
- **Custom builds**: Specialised versions for specific instruments

## Pre-installed Tools

### Astroquery / astropy

The [astroquery tool](https://astroquery.readthedocs.io/en/latest/) is available on newer CASA containers (6.4.4-6.6.3). To use astroquery from an appropriate CASA container:

```bash
# Use the astroquery-compatible Python environment
/opt/casa/bin/python3
```

**Example usage:**
```python
from astroquery.simbad import Simbad
result_table = Simbad.query_object("m1")
result_table.pprint()
```

This yields a table with basic information about M1.

### Analysis Utilities

The [analysisUtils package](https://casaguides.nrao.edu/index.php/Analysis_Utilities) is pre-installed on every CASA container and ready to use:

```python
import analysisUtils as au
```

### ADMIT

[ADMIT (ALMA Data Mining Tool)](https://casaguides.nrao.edu/index.php/ADMIT_Products_and_Usage_CASA_6) is pre-installed on CASA containers where possible (CASA versions 4.5 and higher) and should be ready to use, although it has not been extensively tested.

!!! warning "Version Compatibility"
    The newest CASA containers (6.6.1-pipeline and regular versions 6.6.4 and higher) exclude ADMIT because it does not properly compile.

### Firefox

The Firefox web browser is available for CASA versions 6.1.0 to 6.4.3, needed for CASA commands that interact with weblogs. Error messages may appear in your terminal window, but the browser is functionally sufficient for most CASA weblog tasks.

### UVMultiFit

The [UVMultiFit](https://github.com/onsala-space-observatory/UVMultiFit/blob/master/INSTALL.md) package is installed and working for all CASA 5.X versions except 5.8. To load UVMultiFit:

```python
# In CASA
from NordicARC import uvmultifit as uvm
```

## Troubleshooting
### Known Issues

#### CASA 6.5.0 to 6.5.2 Display Errors

**Problem:** CASA initially launches with display errors in the logger window.

**Solution:** Exit and restart CASA:
```bash
casa     # Initial launch (may show errors)
exit     # Exit CASA
casa     # Restart (errors should be resolved)
```

#### Multi-thread Pipeline Errors

**Problem:** Running multi-thread pipeline scripts (MPI CASA) may generate error messages.

**Reference:** See [CASA FAQ](https://casadocs.readthedocs.io/en/latest/notebooks/frequently-asked-questions.html) under 'Running pipeline in non-interactive mode'.

**Solution:** In Desktop containers, initiate MPI CASA as follows:
```bash
xvfb-run -a mpicasa casa --nologger --nogui -agg -c casa_script.py
```

## Related Containers

### Galario

The UV data analysis package [galario](https://mtazzari.github.io/galario) is available under the radio-submm menu. Note that this container has had minimal testing, and the uvplot package commands in the quickstart.py script are not currently working, although all preceding commands in the quickstart.py script do work.

### Starlink

The JCMT's [Starlink](https://starlink.eao.hawaii.edu/starlink) package is available under the radio-submm menu, including image analysis tools and the gaia image viewer. Note that the [starlink-pywrapper](https://starlink-pywrapper.readthedocs.io/en/latest/) add-on package is not currently working. Minimal testing has been done on the Starlink container.

---

## Related Documentation

- **[Radio Astronomy Guide](../guides/radio-astronomy/index.md)** - Comprehensive radio astronomy workflows
- **[CASA Desktop Workflows](../guides/radio-astronomy/casa-workflows.md)** - Advanced CASA usage patterns
- **[Container Guide](../containers.md)** - General container usage and development
