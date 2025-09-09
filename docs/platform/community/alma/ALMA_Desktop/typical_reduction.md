# Typical ALMA data reduction workflow

A concise overview of a typical reduction and imaging workflow using CASA in Desktop sessions.

First, download your ALMA data onto your Desktop Session (see the archive download tutorials). If you already have the data locally, use one of the file transfer methods to move it into your session.

Next, open a CASA container (see the Start CASA tutorial for the correct version). Start CASA in interactive or pipeline mode depending on your script:

```sh
casa
casa --pipeline
```

Inside CASA run the reduction script (commonly named `scriptForPI.py`):

```py
execfile('scriptForPI.py')
```

After the reduction finishes you will find calibrated measurement sets in a `calibrated/` directory. The `scriptForImaging.py` script (if provided) can be used to create images and is often run from the `calibrated/` directory.

When analysis is complete, transfer final files off the system using one of the transfer options (VOSpace, web download, vcp, etc.). Example using `vcp`:

```sh
vcp calibrated_final_cont_image_162622-24225.* vos:helenkirk/
```

Note: use VOSpace for long-term storage; the Science Portal sessions are not intended as persistent archival storage.
