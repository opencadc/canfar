# CASA Container User Guide

Essential information for using CASA (Common Astronomy Software Applications) containers on CANFAR, including available tools, known issues, and troubleshooting tips.

## Astroquery and Astropy Integration

**What is Astroquery?**  
[Astroquery](https://astroquery.readthedocs.io/en/latest/) is a Python package that provides access to astronomical web services, allowing you to query databases like SIMBAD, Vizier, and ALMA directly from Python.

**Availability**: Astroquery is installed on CASA containers **version 6.4.4 and newer**.

### Using Astroquery

To access astroquery from a CASA container, use the CASA-compatible Python interpreter:

```bash
/opt/casa/bin/python3
```

**Example - Querying SIMBAD for M1:**

```python
from astroquery.simbad import Simbad

# Query basic information about M1 (Crab Nebula)
result_table = Simbad.query_object("m1")
result_table.pprint()
```

This returns a table with basic astronomical data for the Crab Nebula including coordinates, magnitudes, and object type.

## Analysis Utilities Package

**What is Analysis Utilities?**  
The [analysisUtils package](https://casaguides.nrao.edu/index.php/Analysis_Utilities) provides additional tools for CASA data analysis, including plotting utilities and advanced calibration functions.

**Availability**: Pre-installed on **all CASA containers** and ready to use.

### Usage

```python
# Load the package in CASA
import analysisUtils as au

# Example usage
au.plotbandpass('your_bandpass_table.tb')
```

## Web Browser Support

**Firefox Availability**: Firefox web browser is available on CASA versions **6.1.0 to 6.4.3** for viewing weblogs and interactive CASA features.

### Usage Notes
- Some terminal error messages may appear but can be ignored
- Basic functionality is sufficient for viewing CASA weblogs
- For newer CASA versions, access weblogs through the host system browser

## UVMultiFit Package

**What is UVMultiFit?**  
[UVMultiFit](https://github.com/onsala-space-observatory/UVMultiFit/blob/master/INSTALL.md) is a package for fitting models to radio interferometry visibility data.

**Availability**: Installed on **all CASA 5.x versions except 5.8**.

### Usage

```python
# In CASA, load UVMultiFit
from NordicARC import uvmultifit as uvm

# Use UVMultiFit functions
# (see UVMultiFit documentation for specific commands)
```

## Known Issues and Solutions

### 1. Logger Display Errors (CASA 6.5.0-6.5.2)

**Problem**: Display errors appear in the logger window when CASA first launches.

**Solution**: Exit and restart CASA (without restarting the container):

```bash
# First launch (may show errors)
casa

# Exit CASA
exit

# Restart CASA (errors should be resolved)
casa
```

### 2. MPI CASA Pipeline Issues

**Problem**: Multi-threaded pipeline scripts may generate error messages.

**Background**: This is a known issue documented in [CASA FAQ](https://casadocs.readthedocs.io/en/latest/notebooks/frequently-asked-questions.html) under "Running pipeline in non-interactive mode".

**Solution**: For Desktop containers, use the following command to run MPI CASA:

```bash
xvfb-run -a mpicasa casa —nologger —nogui -agg -c casa_script.py
```

**What this does**: 
- `xvfb-run -a`: Provides a virtual display buffer
- `mpicasa`: Enables multi-processing
- `—nologger —nogui -agg`: Disables GUI components that can cause conflicts

## Related Software Containers

### Galario for UV Data Analysis

**What is Galario?**  
[Galario](https://mtazzari.github.io/galario) is a library for disk modeling and UV data analysis, particularly useful for protoplanetary disk research.

**Access**: Available in the **radio-submm** container menu.

**Status**: Basic functionality works, but some features in the quickstart.py script (particularly uvplot commands) are not currently functional.

### Starlink for JCMT Data

**What is Starlink?**  
[Starlink](https://starlink.eao.hawaii.edu/starlink) is the JCMT's software suite for sub-millimeter data reduction and analysis, including image analysis tools and the GAIA image viewer.

**Access**: Available in the **radio-submm** container menu.

**Known Limitations**: 
- [starlink-pywrapper](https://starlink-pywrapper.readthedocs.io/en/latest/) Python interface is not currently working
- Testing has been limited - report issues to [support@canfar.net](mailto:support@canfar.net)

---

## Getting Help

### Container-Specific Issues
- **Error messages**: Include CASA version and container type in support requests  
- **Missing features**: Check [available containers](../reference-material/available-containers.md) for alternatives
- **Version compatibility**: Consider using older containers for legacy scripts

### Support Resources
- **Email**: [support@canfar.net](mailto:support@canfar.net)  
- **CASA Documentation**: [Official CASA Guides](https://casaguides.nrao.edu/)
- **Community**: [CANFAR Slack Channel](https://cadc.slack.com/archives/C01K60U5Q87)
