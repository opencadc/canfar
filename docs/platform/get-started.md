# Get started

Use the CANFAR Science Platform to analyse astronomical data in your browser.
You can run notebooks and astronomy applications near your data, save results,
and share them with your project. You do not need to install the Python client
to follow this guide.

## 1. Get an account and access

Request a [Canadian Astronomy Data Centre (CADC) account](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html).
Ask your project administrator to add you to the group that owns the data you
need. If you need help, contact [CANFAR support](support/index.md).

## 2. Run your first notebook

1. Sign in to the [Science Portal](https://www.canfar.net/science-portal/).
2. In **Launch New Session**, choose **Notebook**, select an image containing
   the software you need, and submit the form. An image is a packaged software
   environment; a Session is your running instance of it.
3. Find your Session under **Active Sessions**. Wait for it to start, then open
   its notebook link.
4. Follow [Create, run, and save a notebook](sessions/notebook.md#create-run-and-save-a-notebook)
   to run your first Python cell and save the notebook in persistent storage.

Choose an image from the portal's current list. Available software and
resource choices depend on the image and server.

## 3. Upload data and save your work

Inside a Session, use these mounted paths when they are available:

| Location | Use |
| --- | --- |
| `/arc/home/USER` | Personal scripts, notebooks, and results; replace `USER` with your username |
| `/arc/projects/PROJECT` | Shared project data and outputs; replace `PROJECT` with your project's directory |
| `/scratch` | Temporary files; deleted with the Session |

Use [browser file transfers](storage/transfers.md#transfer-files-in-your-browser)
to upload inputs or download results. Save and verify your notebook and results
under `/arc` before using the Session's delete control in **Active Sessions**.
Files under `/arc` remain available after deletion. Closing a browser tab alone
does not stop the Session.

Choose [Desktop](sessions/desktop.md), [CARTA](sessions/carta.md), or
[Firefly](sessions/firefly.md) when you need a different analysis interface.

## 4. Automate your analysis (optional)

For repeated work, [install the client](../client/get-started.md#install) and
follow the [command-line tutorial](../cli/quick-start.md) or
[Python tutorial](../client/quick-start.md). Check the installation guide's
release note before using examples from this branch.

To run an unattended workflow:

1. Test your command on a small input in an interactive Session.
2. Set explicit input and output paths in the command or environment.
3. Submit a [headless Session](sessions/batch.md), which runs without a browser interface.
4. Inspect its progress with `canfar ps --all`, `canfar info`, and `canfar events`.
5. Copy final results out of `/scratch` before deleting the Session.

## Next steps

- [Platform concepts](concepts.md)
- [Sessions](sessions/index.md)
- [Storage](storage/index.md)
- [Containers](containers/index.md)
- [Permissions](permissions.md)
- [Support](support/index.md)
