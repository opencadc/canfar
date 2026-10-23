# CARTA Sessions

[CARTA](https://cartavis.org/) is a browser-based tool for inspecting
astronomical images and data cubes. Use it for interactive visualisation and
region or spectral exploration; use a [headless Session](batch.md) for a
repeatable reduction.

<span id="step-4-launch-session"></span>
<span id="for-remote-access"></span>

## Launch CARTA

1. Sign in to the [Science Portal](https://www.canfar.net/science-portal/).
2. In **Launch New Session**, choose **CARTA**, select an image containing
   the software you need, and launch the Session.
3. Wait for it to start under **Active Sessions**, then open its application link.

Save your work under `/arc` before using the Session's delete control in the
portal. Closing the browser tab does not stop the Session. See
[Get started](../get-started.md) for account, storage, and cleanup steps.

### Launch from the command line (optional)

[Install the client](../../client/get-started.md#install) before using these commands.

Choose an image published for the active server:

```bash
canfar login cadc
canfar image ls --kind carta
canfar create carta IMAGE_NAME --name cube-inspection
```

The Science Portal offers the same Session Kind. Available versions, resource
controls, and supported file formats are deployment- and image-specific. Use
the image description rather than assuming a version or startup time.

Monitor the Session and open it when ready:

```bash
canfar ps --all
canfar info SESSION_ID
canfar open SESSION_ID
```

For a Session that remains `Pending`, inspect [events and resource
troubleshooting](batch.md#monitor-and-troubleshoot).

<span id="data-loading"></span>
<span id="supported-file-paths"></span>
<span id="line-profiles"></span>
<span id="session-wont-load-data"></span>

## Open data

CARTA can open files that the Session can read. Common workflows use FITS
images or cubes under mounted Science Platform storage:

```text
/arc/home/<user>/
/arc/projects/<project>/
/scratch/
```

For an object in a configured VOSpace Service, transfer it explicitly before
opening it:

```bash
canfar data cp IDENTIFIER:/path/to/cube.fits local:/scratch/cube.fits
```

Use the Storage Identifier and path supplied by your project. `/scratch` is
temporary; copy any regions, tables, or derived products that must survive to
`/arc` or a persistent VOSpace Service. See [Data transfers](../storage/transfers.md).

<span id="overview"></span>
<span id="key-features"></span>
<span id="data-format-support"></span>
<span id="creating-a-carta-session"></span>
<span id="step-1-select-session-type"></span>
<span id="step-2-choose-container-version"></span>
<span id="available-versions"></span>
<span id="step-3-configure-session"></span>
<span id="session-name"></span>
<span id="resource-allocation"></span>
<span id="using-carta"></span>
<span id="first-steps"></span>
<span id="from-canfar-storage"></span>
<span id="interface-overview"></span>
<span id="main-components"></span>
<span id="essential-controls"></span>
<span id="analysis-features"></span>
<span id="spectral-analysis"></span>
<span id="moment-maps"></span>
<span id="region-analysis"></span>
<span id="creating-regions"></span>
<span id="statistical-analysis"></span>
<span id="animation-and-navigation"></span>
<span id="data-cube-navigation"></span>
<span id="multi-panel-views"></span>
<span id="optimisation-tips"></span>
<span id="collaboration-features"></span>
<span id="real-time-sharing"></span>
<span id="best-practices-for-collaboration"></span>
<span id="advanced-features"></span>
<span id="scripting-and-automation"></span>
<span id="export-capabilities"></span>
<span id="integration-with-other-tools"></span>
<span id="custom-colour-maps"></span>
<span id="display-problems"></span>

## Interactive analysis

The exact controls depend on the CARTA version, but typical workflows are:

1. open an image or cube from the Session filesystem;
2. inspect WCS, channels, Stokes axes, and image statistics;
3. draw regions and examine spectra or moment summaries; and
4. export regions, tables, or figures to a persistent path.

Treat exported files as products of the analysis and record the input path,
image version, and CARTA version with them.

<span id="performance-optimisation"></span>
<span id="large-dataset-handling"></span>
<span id="memory-management"></span>
<span id="network-performance"></span>
<span id="slow-performance"></span>

## Performance

Large cubes can require substantial memory, storage, and network traffic. Start
with a representative sub-cube, close unused views, and stage a remote object
to `/scratch` when repeated reads are required. Request only measured CPU or
memory needs; fixed oversized requests may wait for matching capacity.

<span id="common-issues"></span>
<span id="connection-issues"></span>

## Troubleshooting

- If the image is not listed, confirm the image with `canfar image ls --kind
  carta` and ask the deployment operator about availability.
- If a file does not open, verify the path with `canfar data info` or stage a
  copy and check its format.
- If the interface is slow, reduce the data subset and inspect Session
  resources before increasing the request.
- If the browser disconnects, check `canfar ps --all` and `canfar info` before
  restarting the Session.

See [Support](../support/index.md) for the diagnostic information to include
when reporting a persistent problem.
