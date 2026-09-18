# Frequently asked questions

## What is the CANFAR Science Platform?

CANFAR provides interactive and unattended computing Sessions for astronomy,
with access to project storage, configured VOSpace Services, and published
Container Images. The available Servers, images, resources, and Storage
Identifiers depend on the deployment and your account.

<span id="cant-access-files-or-storage"></span>
<span id="authentication-and-access-issues"></span>
<span id="permission-denied-errors"></span>

## How do I get access?

You need a CADC account and access to a Science Platform Server. Request a
[CADC account](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html)
if needed. Then either ask your project's administrator to add you to its
group, or email [support@canfar.net](mailto:support@canfar.net) with your CADC
username and a short description of your research. See
[Getting started](../get-started.md).

<span id="who-can-use-it-and-what-does-it-cost"></span>

## Who can use CANFAR and what does it cost?

The CADC deployment serves Canadian astronomers and their collaborators.
Access is provided for astronomical research, under the site's policies and
within the storage and compute allocated to your project; it is not a
general-purpose free cloud. A project that needs more than CANFAR can offer
should apply for an [Alliance resource allocation](https://docs.alliancecan.ca/).
An SRCNet Science Platform Server has its own eligibility rules and support
contacts.

<span id="authentication-options-for-programs"></span>
<span id="how-do-i-authenticate"></span>

## How do I log in and select a server?

For browser work, sign in to the [Science Portal](https://www.canfar.net/science-portal/)
and launch a Session. You do not need to install the client.

For command-line or Python work, [install the client](../../client/get-started.md#install)
and select your server:


```bash
canfar login cadc
canfar server ls
canfar server use SERVER_NAME
canfar config get active.server
```

`canfar auth` manages saved Authentication Records and `canfar server` manages
the active Server. The removed `canfar context` command is not part of the
current CLI.

<span id="what-session-types-are-available-and-when-should-i-use-them"></span>
<span id="how-long-can-sessions-run"></span>
<span id="can-i-automate-session-management-with-the-python-client"></span>
<span id="can-i-run-multiple-sessions-at-once"></span>
<span id="sessions-wont-start-or-take-too-long-to-launch"></span>

## Which Session Kind should I use?

- `notebook` for interactive Python and exploratory work;
- `desktop` for a graphical Linux environment;
- `carta` for image and cube visualisation;
- `firefly` for supported browser-based astronomy applications; and
- `headless` for scripts, reductions, and parameter sweeps.

Use `canfar image ls --kind KIND` to see images available for a kind. See
[Sessions](../sessions/index.md).

<span id="troubleshooting-slow-or-failing-sessions"></span>
<span id="why-is-my-session-stuck-in-pending"></span>
<span id="i-cant-connect-to-my-session-url"></span>
<span id="troubleshooting"></span>
<span id="performance-is-slow-or-variable"></span>

## What does `Pending` mean?

`Pending` means the platform accepted the request but has not made the Session
ready. Admission, requested resources, image pulling, or initialization can
all occur while a Session is Pending. `canfar create` returns accepted IDs; it
does not wait for `Running`.

In the browser, check the Session in **Active Sessions** and wait for its
application link. If it remains pending, record its ID and contact
[support](index.md). With the client installed, collect more details:

```bash
canfar ps --all
canfar info SESSION_ID
canfar events SESSION_ID
canfar stats
```

Do not assume that headless work has priority over interactive work. Queue
policy is deployment-owned. See [batch processing](../sessions/batch.md).

## What does `canfar create` print?

Human mode reports the accepted Session ID. JSON and YAML modes emit the raw
list of returned IDs, suitable for a script:

```bash
canfar create headless IMAGE_NAME --output json -- python run.py
```

Put CLI options before the `--` delimiter; everything after it is the command
given to the container. A partial result contains the IDs accepted by the
platform. An empty result indicates a creation or transport failure, not a
queued Session.

<span id="how-much-storage-do-i-get-and-where-should-i-put-data"></span>
<span id="how-do-i-transfer-large-datasets"></span>
<span id="how-do-i-check-platform-status-and-quotas-from-the-cli"></span>

## Where should I put data?

- `/arc/home/<user>/` for personal persistent files;
- `/arc/projects/<project>/` for project files, when that path is available;
- a configured VOSpace Service for persistent remote data; and
- `/scratch` for temporary, high-speed staging only.

Use explicit `IDENTIFIER:/path` operands with `canfar data`. See [Storage](../storage/index.md)
and [Data transfers](../storage/transfers.md).

## How do I use storage from Python?

The public API uses explicit identifiers:

```python
from canfar.storage import filesystem, identifiers

print(identifiers())
remote = filesystem("IDENTIFIER")
try:
    print(remote.ls("/path"))
finally:
    remote.close()
```

`local` is the machine running the Python process. CANFAR does not register a
dynamic `vault://` or `arc://` protocol and there is no `storage.configure()`
call. See [Filesystem and Python tools](../storage/filesystem.md).

<span id="can-i-run-gpuaccelerated-workloads"></span>
<span id="session-resources"></span>
<span id="why-is-my-session-performance-variable"></span>
<span id="community-resources"></span>

## Can I use a GPU or request more resources?

Use the resource options supported by the current `canfar create --help` and
the image's requirements. A larger fixed request can wait longer for matching
capacity. Record the image and resource request with a reproducible workflow.
Ask the platform operator about deployment-specific GPU availability.

<span id="what-softwarecontainers-are-available"></span>

## How do I build or publish a Container Image?

Start with [Container Images](../containers/index.md) and the registry
instructions for your project. Use a stable tag or digest and never store
credentials in an image layer. A pushed image is usable only where the target
Science Platform Server can pull it.

<span id="platform"></span>
<span id="can-i-install-additional-software"></span>
<span id="collaboration-and-sharing"></span>
<span id="getting-help-and-community"></span>
<span id="client"></span>
<span id="how-do-i-call-the-rest-api-directly"></span>
<span id="cli"></span>
<span id="where-can-i-find-more-cli-help"></span>
<span id="common-platform-issues"></span>
<span id="browser-or-interface-problems"></span>
<span id="certificate-problems"></span>
<span id="getting-help"></span>
<span id="when-to-use-each-support-channel"></span>
<span id="use-discord-for"></span>
<span id="use-github-issues-for"></span>
<span id="email-support-for"></span>
<span id="before-contacting-support"></span>
<span id="what-to-include-in-support-requests"></span>
<span id="response-time-expectations"></span>

## How do I get help?

Run the checks in [Support](index.md), then email
[support@canfar.net](mailto:support@canfar.net) with a Server Name, timestamp,
exact error, and relevant Session diagnostics. Remove tokens, certificates,
passwords, and private data before sharing logs.
