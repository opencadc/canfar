# ALMA analysis workflow

Use this workflow to move ALMA data into a CANFAR Session, reduce it with
CASA, inspect the products, and keep the results in persistent storage. It is
text-first so commands can be copied and the workflow remains useful when the
Science Portal layout changes.

## Prerequisites

- A [CADC account](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html)
  and access to the [CANFAR Science Platform](https://www.canfar.net/). Contact
  [support@canfar.net](mailto:support@canfar.net) if your account or project
  access is not ready.
- A persistent destination: use `/arc/home/[username]` for personal files or
  `/arc/projects/[project]` for shared work. Treat `/scratch` as temporary;
  it is suitable for fast intermediate files, not final results.
- A Session Kind that matches the task: use **Desktop** for CASA and other GUI
  applications, **Notebook** for Python-based analysis, and **CARTA** for
  inspecting images and spectral cubes.
- Optional command-line access. Install the shipped client and log in:

    ```bash
    pip install canfar --upgrade
    canfar login cadc
    canfar auth show
    canfar server ls
    ```

See [Getting Started](../../get-started.md) for account and portal setup.

## Workflow

### 1. Choose a Session and storage location

From the Science Portal, create a Desktop, Notebook, or CARTA Session and
choose an image that supports the application you need. From a terminal, list
the available images before creating a Session:

```bash
canfar image ls --kind desktop
canfar create desktop IMAGE_NAME --name alma-reduction
canfar ps --kind desktop
canfar open [session-id]
```

Replace bracketed values with the Session ID, username, and project name used
by your account. Replace `IMAGE_NAME` with an image returned by
`canfar image ls --kind desktop` that includes the CASA version required by the
reduction. The image listing is the source of truth; do not assume that a CASA
tag remains unchanged.

### 2. Stage the archive data

Download the requested data from the [ALMA Science Archive](https://almascience.nrao.edu/)
to your local machine, or use a configured CANFAR data source. Create a
destination and verify the copy with the CANFAR data commands:

```bash
canfar data mkdir -p arc:/home/[username]/alma/raw
canfar data cp local:/path/to/alma-data.tar.gz \
    arc:/home/[username]/alma/raw/alma-data.tar.gz
canfar data ls -lh arc:/home/[username]/alma/raw
```

The `local:` source is the machine where the command runs. To copy data that
is already in Vault, use a `vault:` source instead:

```bash
canfar data cp vault:/ALMA/test-data/cutouts/test-4d-cube.fits \
    arc:/home/[username]/alma/raw/test-4d-cube.fits
```

Inside a Session, the same `/arc` paths are available from the file browser
and terminal. For a large reduction, copy working data to `/scratch` and keep
the source and final products under `/arc`.

### 3. Start CASA in a Desktop Session

In a Desktop Session, open **Applications → Astro Software**, choose the CASA
version required by the project, and open its terminal. Start CASA in the
mode required by the supplied reduction script:

```bash
casa
casa --pipeline
```

Run the archive's supplied calibration and imaging scripts using the command
form documented for that CASA release. Keep the scripts, measurement sets,
and intermediate products under a persistent project directory or copy them
back to `/arc` when the reduction finishes. The [CASA containers guide](../CASA_and_more.md)
lists version-specific package notes and known issues.

### 4. Inspect and analyse the products

Open calibrated measurement sets or image products from a CARTA Session when
you need cube navigation, spectra, regions, or moment-map inspection. Use a
Notebook Session for Python analysis. Both Session Kinds can read files saved
under `/arc/home/[username]` and `/arc/projects/[project]`.

For a local or scripted check, list the result before opening it:

```bash
canfar data ls -lh arc:/home/[username]/alma/results
canfar data info arc:/home/[username]/alma/results/result.fits
```

### 5. Save results and clean up

Copy final products out of `/scratch` before stopping the Session. From inside
the Session, use ordinary filesystem commands:

```bash
mkdir -p /arc/home/[username]/alma/results
cp -a /scratch/alma-reduction/results/. \
    /arc/home/[username]/alma/results/
```

From the machine where the files are local, use the data command instead:

```bash
canfar data cp local:/path/to/result.fits \
    arc:/home/[username]/alma/results/result.fits
canfar data ls -lh arc:/home/[username]/alma/results
```

When the results are safely stored, inspect and remove the Session if it is no
longer needed:

```bash
canfar info [session-id]
canfar delete [session-id] --force
```

## Expected results

At the end of the workflow:

1. `canfar auth show` reports the active Authentication and
   `canfar server ls` lists an available Science Platform Server.
2. The selected Session reaches `Running` and opens in the Science Portal.
3. Raw data and final products are visible under the chosen `/arc` path from
   the Desktop, Notebook, or CARTA Session.
4. CASA scripts complete using a compatible image, and the reduction products
   are stored outside `/scratch`.
5. Deleting the Session does not remove the files saved under `/arc`.

## Troubleshooting

| Symptom | Check or fix |
| --- | --- |
| Login fails or credentials are stale | Run `canfar --log-level debug login cadc --force`, then `canfar auth show`. |
| No suitable image appears | Run `canfar image ls --kind desktop` (or `--kind notebook`/`--kind carta`) and choose an image that includes the required software. |
| Session remains pending | Run `canfar ps --all`, `canfar events [session-id]`, and `canfar stats`; reduce requested resources if the Science Platform Server has no capacity. |
| A data copy fails | Confirm the `local:`, `arc:`, or `vault:` source and destination with `canfar data ls -lh IDENTIFIER:/path`; check that the active Authentication Record can access the target. |
| Files disappear after the Session ends | Move them from `/scratch` to `/arc/home/[username]` or `/arc/projects/[project]` before deleting the Session. |
| A shared project path is denied | Ask the project administrator to add your CADC account to the project group; see [Permissions](../../permissions.md). |
| CASA is missing or incompatible | Select a Desktop image that lists the required CASA version and match the version to the archive scripts. If CASA 6.5.0–6.5.2 opens with display errors, exit CASA and start it again. |
| A transfer reports expired credentials | Renew or select the Authentication Record used by the active server, then retry. See [support](../../support/index.md) if the record or certificate cannot be refreshed. |
| The browser cannot connect to a new Session | Wait for the Session to reach `Running`, then retry `canfar open [session-id]`; inspect `canfar info [session-id]` and `canfar logs [session-id]` if it still fails. |

## Related documentation

- [Interactive Sessions](../../sessions/index.md), [Desktop](../../sessions/desktop.md),
  [Notebooks](../../sessions/notebook.md), and [CARTA](../../sessions/carta.md)
- [Storage overview](../../storage/index.md), [data transfers](../../storage/transfers.md),
  and [VOSpace](../../storage/vospace.md)
- [CLI quickstart](../../../cli/quick-start.md) and [CLI reference](../../../cli/cli-help.md)
- [Python quickstart](../../../client/quick-start.md)
- [Support](../../support/index.md)
