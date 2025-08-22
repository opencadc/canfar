# Frequently Asked Questions

This unified FAQ covers the CANFAR Science Platform across three areas: Platform, Client, and CLI.

## Platform

### What is the CANFAR Science Platform?
The CANFAR Science Platform is a national cloud computing environment tailored for astronomy. It provides interactive notebooks and desktops, contributed applications (e.g., CARTA, Firefly), batch jobs, and direct access to CADC data holdings.

### Who can use it and what does it cost?
CANFAR is free for astronomical research. Canadian astronomers and their collaborators can use it subject to fair‑use and allocation limits. For larger needs, request additional resources via the Digital Research Alliance of Canada (DRAC) Resource Allocation Competition.

### How do I get access?
1. To start, you must have a CADC account. If you don't have a CADC account, you can request one at: [https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html)
2. To get CANFAR access, send a short e-mail to support@canfar.net with a short note about who you are, your research and what you plan to do with CANFAR. Include your CADC username. Turnaround is typically 1-2 business days. This can be done in parallel with requesting a CADC account.
3. Alternatively, if you already have a CADC account and you are part of a research group that is already using CANFAR, you can ask your PI to add you to the appropriate project groups.

### What session types are available and when should I use them?
- Notebook: Jupyter Lab for interactive analysis and prototyping.
- Desktop: Full Linux desktop for GUI workflows and multi‑app sessions.
- Firefly: Interactive database access and visualization.
- CARTA: Specialized image/cube visualization.
- Headless: Non‑GUI batch processing and automation.

### How long can sessions run?
- Interactive sessions: up to 7 days of continuous runtime, with auto‑shutdown after prolonged inactivity; resumable if not deleted.
- Batch jobs: no strict time limit; queue priority depends on resource usage.

### Can I run GPU‑accelerated workloads?
Yes. Request GPUs in the session configuration (e.g., NVIDIA Tesla/RTX). Ensure your chosen container supports GPU computing.

### How much storage do I get and where should I put data?
- Personal: `/arc/home/[username]/` (e.g., 10 GB typical).
- Project/group: `/arc/projects/[group]/` (hundreds of GB to TBs, varies by project). If you don't already have a project space, you can request one by e-mailing suport@canfar.net.
- Temporary: `/tmp/` inside sessions (cleared when the session ends).
Suggested layout: raw → `/arc/projects/[group]/raw/`, working → `/arc/projects/[group]/data/`, results → `/arc/projects/[group]/results/`, scripts → `/arc/projects/[group]/scripts/`.

### How do I transfer large datasets?
- For files <1 GB, the Science Portal file manager is convenient.
- For larger transfers, use `rsync`/`scp` or VOSpace for very large files (>10 GB).

Example:
```bash
rsync -avz --progress source/ username@canfar.net:/arc/projects/mygroup/
cadc-data put largefile.fits vos:myproject/data/
```

### What software/containers are available?
Containers include general astronomy stacks (AstroPy ecosystem), Jupyter, full Linux desktops, and specialized tools (CASA, CARTA, DS9, TOPCAT). You can also build and use custom containers. See the Container Guide at `platform/containers.md`.

### Can I install additional software?
- Temporary (inside a running session): `pip install --user ...` or system packages if permitted.
- Permanent: build a custom container with your required stack (see `platform/containers.md`).

### Collaboration and sharing
- Share sessions for real‑time collaboration (view or full access).
- Share data via project groups and `/arc/projects/[group]/` with appropriate permissions.
- Share code via Git and group storage; document workflows.

### Troubleshooting slow or failing sessions
- Resource constraints: try fewer cores/less RAM, different time of day, or a different container.
- Container issues: verify name/version; try a maintained baseline image.
- Account/group issues: confirm group membership and active account status.
- Performance: process data in fast scratch (e.g., `/tmp/`), parallelize where appropriate, monitor with `htop`, `df -h`, `iotop`.

### Where are my files?
- Personal: `/arc/home/$(whoami)/`
- Group: `/arc/projects/`
- Temporary: session‑local `/tmp/` (deleted at end of session)

### Getting help and community
- Documentation: start at `platform/home.md` and `platform/guides/index.md`.
- Help & Support: `platform/help.md` (how to contact support and what to include).
- Community: Discord for Q&A and announcements; workshops and office hours are announced there.


## Client

### Can I automate session management with the Python client?
Yes. The Python client supports creating, monitoring, and cleaning up sessions programmatically.

Example:
```python
import time
from canfar import Session

session = Session()
sid = session.create(name="automated", kind="headless", cmd="python", args=["script.py"])

while session.info(sid)[0]["status"] != "Completed":
    time.sleep(60)

session.logs([sid])
session.destroy([sid])
```

### How do I call the REST API directly?
You can use REST endpoints for jobs and sessions if you prefer low‑level control.

Example:
```python
import requests

response = requests.post(
    "https://ws-uv.canfar.net/skaha/v0/session",
    headers={"Authorization": f"Bearer {token}"},
    data={
        "name": "automated-analysis",
        "image": "images.canfar.net/skaha/astroml:latest",
        "cores": 4,
        "ram": 16,
        "kind": "headless",
        "cmd": "python /arc/projects/myproject/analyze.py",
    },
)
response.raise_for_status()
```

### How do I access VOSpace programmatically?
Use CADC client libraries to interact with VOSpace objects.

Example:
```python
from cadcdata import CadcDataClient

client = CadcDataClient()
client.put_file("local_file.fits", "vos:myproject/data/file.fits")
```

### Authentication options for programs
- X.509 certificates (typical for many users).
- OIDC tokens via SRCNet for advanced and cross‑site workflows. See `cli/authentication-contexts.md` for options and flows.


## CLI

### How do I authenticate?
- Certificates:
```bash
cadc-get-cert -u <username>
```
- OIDC (SRCNet‑aware):
```bash
canfar auth login
```

Certificates typically last ~10 days; renew as needed.

### How do I check platform status and quotas from the CLI?
```bash
canfar stats
```

### Why is my session stuck in "Pending"?
Possible reasons: insufficient resources, image issues, quota limits, or maintenance windows. Inspect events:
```bash
canfar events <session-id>
```

### I can’t connect to my session URL
1. Ensure the session is Running (`canfar ps`).
2. Check for VPN/firewall interference.
3. Try another browser or clear cache/private mode.

### Can I run multiple sessions at once?
Yes. You can run multiple sessions concurrently subject to fair‑use and any configured limits per session type. Prefer batch/headless for automation.

### Where can I find more CLI help?
- Quick start: `cli/quick-start.md`
- Auth contexts: `cli/authentication-contexts.md`
- Command reference: `cli/cli-help.md`

