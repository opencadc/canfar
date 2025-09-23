# CASA containers and adjacent software

This page contains a summary of additional packages included in CASA containers, known issues and work-arounds for specific containers, as well as a brief summary on other radio astronomy tools available.

## CASA add-on tools and packages

### Astroquery / Astropy
The [astroquery tool](https://astroquery.readthedocs.io/en/latest/) is presently only installed on newer CASA containers (6.4.4 and above).  To use astroquery from an appropriate CASA container, type the following to initiate an astroquery-compatible version of python:
```bash
/opt/casa/bin/python3
```
As per the [astroquery documentation](https://astroquery.readthedocs.io/en/latest/), the tool can then be used on the command line within the python environment.  For example, the following sequence of commands yield a one-line table listing some basic information about M1.

```python
from astroquery.simbad import Simbad
result_table = Simbad.query_object("m1")
result_table.pprint()
```

### Analysis Utilities
The [analysisUtils package](https://casaguides.nrao.edu/index.php/Analysis_Utilities) package is pre-installed on every CASA container, and is ready to use.  You may need to type the following to load the package:

```python       
import analysisUtils as au
```

### Firefox
The Firefox web-browser, needed for CASA commands where you are interacting with the weblogs, should available for CASA versions 6.1.0 to 6.4.3.  Error messages will pop up in your terminal window, but minimal testing suggests that it is sufficiently functional.

### UVMultiFit
The [UVMultiFit](https://github.com/onsala-space-observatory/UVMultiFit/blob/master/INSTALL.md) package is presently installed and working for all CASA 5.X versions except 5.8.  To load the UVMultiFit package, initiate casa and then type

```python
from NordicARC import uvmultifit as uvm
```
## Known Issues

1. CASA versions `6.5.0` to `6.5.2` initially launch with some display errors in the logger window.  Exiting casa (but not the container) and re-starting casa fixes the issue, i.e.,

    ```bash
    casa
    exit
    casa
    ```

2. Running multi-thread pipeline scripts (MPI CASA) may generate error messages, as described [here](https://casadocs.readthedocs.io/en/latest/notebooks/frequently-asked-questions.html) under the 'Running pipeline in non-interactive mode' section.  A CANFAR ALMA user reports success initiating MPI CASA in a Desktop container as follows:

    ```bash
    xvfb-run -a mpicasa casa —nologger —nogui -agg -c casa_script.py
    ```

## CASA Adjacent Containers 

### Galario
The UV data analysis package [galario](https://mtazzari.github.io/galario) is available under the radio-submm menu.  Note that this container has had minimal testing, and the uvplot package commands in the quickstart.py script are not presently working, although all preceeding commands in the quickstart.py script do work.

### Starlink
The JCMT's [Starlink](https://starlink.eao.hawaii.edu/starlink) package is available under the radio-submm menu, including image analysis tools and the gaia image viewer.  Note that the [starlink-pywrapper](https://starlink-pywrapper.readthedocs.io/en/latest/) add-on package is presently not working.  Minimal testing has been done on the Starlink container.


