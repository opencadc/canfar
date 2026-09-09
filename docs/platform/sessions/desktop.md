# Desktop Sessions

A Desktop Session provides a browser-accessible graphical Linux environment.
Use it for tools that need a window manager, multiple graphical applications,
or an interactive terminal. Use a Notebook or headless Session when a browser
desktop is unnecessary.

## Launch a Desktop

1. Sign in to the [Science Portal](https://www.canfar.net/science-portal/).
2. In **Launch New Session**, choose **Desktop**, select an image containing
   the software you need, and launch the Session.
3. Wait for it to start under **Active Sessions**, then open its application link.

Save your work under `/arc` before using the Session's delete control in the
portal. Closing the browser tab does not stop the Session. See
[Get started](../get-started.md) for account, storage, and cleanup steps.

### Launch from the command line (optional)

[Install the client](../../client/get-started.md#install) before using these commands.

List the images available on the active server and choose one that contains
the software you need:

```bash
canfar login cadc
canfar image ls --kind desktop
canfar create desktop IMAGE_NAME --name visual-analysis
```

You can also launch from the Science Portal. Image contents, desktop
environment, GPU availability, and resource controls are deployment-specific.
Do not assume that an application shortcut or astronomy package is present in
every image.

Monitor and open the Session when it is ready:

```bash
canfar ps --all
canfar info SESSION_ID
canfar open SESSION_ID
```

If it remains `Pending`, inspect `canfar events SESSION_ID`; see [batch
troubleshooting](batch.md#monitor-and-troubleshoot).

## Files and applications

The desktop terminal and file manager see the Session's mounted paths:

```text
/arc/home/<user>/          personal persistent files
/arc/projects/<project>/   project files, when available
/scratch/                  temporary staging
```

Save data, scripts, and exported results under `/arc` or a persistent VOSpace
Service. `/scratch` is deleted when the Session ends. For remote objects that
are not mounted, use [CANFAR data transfers](../storage/transfers.md) before
opening them in a path-oriented application.

Some deployments expose scientific software through [CVMFS](../cvmfs.md).
It is read-only and its repositories and modules vary by server. Record the
module and version if a workflow depends on it.

## Good desktop practice

- Keep the graphical Session for exploration, visual inspection, and tools
  that genuinely need a display.
- Save work before deleting or restarting a Session; a browser Session is not
  a durable data store.
- Use a named Container Image or versioned environment for repeatable software
  rather than installing packages only in the current Session.
- Copy final products to persistent storage before closing the Session.

## Troubleshooting

- If the image is missing, confirm it with `canfar image ls --kind desktop`.
- If the Session is Running but the desktop does not open, retry the link in a
  current browser and report the Session ID and endpoint error.
- If a file is missing or forbidden, verify the identifier/path and project
  membership with `canfar data info` and the project administrator.
- If the desktop is slow, close unused applications and inspect the Session's
  resource usage before requesting more CPU or memory.

See [Support](../support/index.md) for a minimal diagnostic report.
