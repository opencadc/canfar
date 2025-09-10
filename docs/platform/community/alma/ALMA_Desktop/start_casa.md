# Starting CASA in a Desktop session

How to launch CASA inside a Desktop session and run reduction or imaging scripts.

CASA (Common Astronomy Software Applications) is typically provided as a container in the Desktop session. To start CASA:

1. Launch a Desktop session and open a terminal.
2. Start the CASA container. Depending on the configuration the command may be as simple as:

```sh
casa
```

3. If you have a reduction script (e.g., `scriptForPI.py`) you can run it within CASA:

```py
execfile('scriptForPI.py')
```

If your dataset requires a specific CASA version, choose the container image for that version.
the scripts distributed with ALMA Cycle 0 data on the archive).
to use a non-CASA terminal for all regular linux uses.

Once you have launched a Desktop session it is straightforward to run CASA in a terminal.

![image](../../../sessions/images/desktop/1_launch_desktop.png)

To start a CASA-enabled terminal, click the `Applications` menu at the top-left of the screen and choose the desired CASA version from the `AstroSoftware` menu.

Select the CASA version you want. All versions back to CASA 3.4.0 are available; choose the one appropriate for your scripts.

Clicking a CASA version opens a terminal where you can start CASA with `casa` or `casa --pipeline` (two dashes before `pipeline`).

You can open a regular (non-CASA) terminal by double-clicking the `terminal` icon. CASA terminals accept a limited set of commands; use the non-CASA terminal for general Linux work.
