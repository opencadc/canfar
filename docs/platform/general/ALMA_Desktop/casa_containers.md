# General notes on CASA containers 

This page contains a compilation of useful notes, etc, on various CASA containers.

## Astroquery / astropy

The [astroquery tool](https://astroquery.readthedocs.io/en/latest/) is presently only installed on the very latest CASA containers (>6.6), but will be installed in earlier versions as time permits.  To use astroquery from an appropriate CASA container, type the following to initiate an astroquery-compatible version of python:
`/opt/casa/bin/python3`
As per the [astroquery documentation](https://astroquery.readthedocs.io/en/latest/), the tool can then be used on the command line within the python environment.  For example, the following sequence of commands
`from astroquery.simbad import Simbad`
`result_table = Simbad.query_object("m1")`
`result_table.pprint()`
yield a one-line table listing some basic information about M1.

## Analysis Utilities
The [analysisUtils package](https://casaguides.nrao.edu/index.php/Analysis_Utilities) package is pre-installed on every CASA container, and is ready to use.  You may need to type
`import analysisUtils as au`
to load it.

## UVMultiFit
The [UVMultiFit](https://github.com/onsala-space-observatory/UVMultiFit/blob/master/INSTALL.md) package is presently installed and working for all CASA 5.X versions except 5.8.  To load the UVMultiFit package, initiate casa and then type
`from NordicARC import uvmultifit as uvm`

## Known Container Bugs
CASA versions 6.5.0 to 6.5.2 initially launch with some display errors in the logger window.  Exiting casa (but not the container) and re-starting casa fixes the issue, i.e.,
`casa`
`exit`
`casa`


