# Desktop Sessions

A Desktop Session provides a browser-accessible graphical Linux environment.
Use it for tools that need a window manager, multiple graphical applications,
or an interactive terminal. Use a Notebook or headless Session when a browser
desktop is unnecessary.

<span id="overview"></span>
<span id="common-use-cases"></span>
<span id="how-desktop-sessions-work"></span>
<span id="creating-a-desktop-session"></span>
<span id="step-1-select-session-type-and-name"></span>
<span id="step-2-configure-resources"></span>
<span id="step-3-launch-session"></span>
<span id="desktop-environment"></span>
<span id="key-desktop-features"></span>
<span id="desktop-architecture"></span>
<span id="1-desktop-shortcuts"></span>
<span id="method-1-desktop-shortcuts"></span>
<span id="desktop-session-features"></span>
<span id="storage-access"></span>
<span id="collaboration-and-sharing"></span>
<span id="session-sharing"></span>
<span id="collaborative-workflows"></span>

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

<span id="available-software"></span>
<span id="2-astro-software-menu"></span>
<span id="available-applications"></span>
<span id="native-vs-container-applications"></span>
<span id="cvmfs-software-repositories"></span>
<span id="working-with-applications"></span>
<span id="launching-applications"></span>
<span id="method-2-astro-software-menu"></span>
<span id="method-3-file-association"></span>
<span id="example-multi-application-workflow"></span>
<span id="casa-desktop-usage"></span>
<span id="file-management"></span>
<span id="file-operations"></span>
<span id="file-transfer"></span>

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

<span id="session-persistence"></span>
<span id="best-practices-for-collaboration"></span>

<span id="font-size-adjustment"></span>
<span id="changing-terminal-font-size"></span>

## Make text easier to read

In a Desktop terminal, open its preferences from the menu or context menu and
increase the font size. Other desktop applications have their own font or
display preferences; changing browser zoom may only enlarge the surrounding
portal controls.

In a Notebook Session, use JupyterLab's settings for editor fonts or your
browser's zoom controls for the interface.

<span id="copy-paste-between-containers"></span>
<span id="accessing-the-clipboard"></span>
<span id="using-the-clipboard-for-text-transfer"></span>

## Copy and paste text

Inside a Desktop terminal, select text and use **Ctrl+Shift+C** to copy and
**Ctrl+Shift+V** to paste, or use the terminal's copy/paste menu items.
Other applications may use **Ctrl+C** and **Ctrl+V**.

To move text between your computer and the remote desktop, use the desktop
connection's clipboard control when available. Browser clipboard permissions
and the chosen desktop image can affect direct keyboard paste. If it fails,
save the text as a file and [upload or download it](../storage/transfers.md#transfer-files-in-your-browser).
Use file transfers for datasets and long scripts.

## Good desktop practice

- Keep the graphical Session for exploration, visual inspection, and tools
  that genuinely need a display.
- Save work before deleting or restarting a Session; a browser Session is not
  a durable data store.
- Use a named Container Image or versioned environment for repeatable software
  rather than installing packages only in the current Session.
- Copy final products to persistent storage before closing the Session.

<span id="connecting-to-your-desktop"></span>
<span id="initial-connection"></span>

## Troubleshooting

- If the image is missing, confirm it with `canfar image ls --kind desktop`.
- If the Session is Running but the desktop does not open, retry the link in a
  current browser and report the Session ID and endpoint error.
- If a file is missing or forbidden, verify the identifier/path and project
  membership with `canfar data info` and the project administrator.
- If the desktop is slow, close unused applications and inspect the Session's
  resource usage before requesting more CPU or memory.

See [Support](../support/index.md) for a minimal diagnostic report.
