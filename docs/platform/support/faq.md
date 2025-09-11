# Frequently Asked Questions

!!! abstract "🎯 Quick Navigation"
    **Find answers by topic:**
    
    - **[Platform Questions](#platform)**: Getting started, sessions, storage, performance
    - **[Session Resources](#session-resources)**: Resource management and optimisation
    - **[Client Questions](#client)**: Python client automation and REST API usage
    - **[CLI Questions](#cli)**: Command-line interface and authentication
    - **[Troubleshooting](#troubleshooting)**: Common problems and solutions

This unified FAQ covers the CANFAR Science Platform across all areas: Platform, Client, and CLI usage.

## Platform

### What is the CANFAR Science Platform?
The CANFAR Science Platform is a national cloud computing environment tailored for astronomy. It provides interactive notebooks and desktops, browser-native visualization (e.g., CARTA, Firefly), user-contributed web applications, batch jobs, and direct access to CADC data holdings.

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
- CARTA: Specialised image/cube visualisation.
- Headless: Non‑GUI batch processing and automation.

### How long can sessions run?
- Interactive sessions: up to 7 days of continuous runtime, with auto‑shutdown after prolonged inactivity; resumable if not deleted.
- Batch jobs: no strict time limit; queue priority depends on resource usage.

### Can I run GPU‑accelerated workloads?
Yes. Request NVIDIA GPUs in the session configuration from the command line or the API. Ensure your chosen container supports CUDA libraries (i.e. `astroml-cuda`)


### How much storage do I get and where should I put data?

- Personal: `/arc/home/[user]/` (typically 10 GB).
- Project/group: `/arc/projects/[project]/` (hundreds of GB to TBs, varies by project). If you do not have a project space, request one by emailing support@canfar.net.
- Temporary: `/scratch/` inside sessions (cleared when the session ends).

Suggested layout:

- Raw data: `/arc/projects/[project]/raw/`
- Working data: `/arc/projects/[project]/working/`
- Data: `/arc/projects/[project]/data/`
- Results: `/arc/projects/[project]/results/`
- Scripts: `/arc/projects/[project]/scripts/`


### How do I transfer large datasets?

- For files <1 GB, the Science Portal file manager is convenient.

or the VOSpace client `vcp` from the `vos` python package:

- For larger transfers, you can use `sshfs`:

    ```bash
    sshfs -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=10,defer_permissions -p 64022 [user]@ws-uv.canfar.net:/ $HOME/arc
    cp largedata.fits $HOME/arc/projects/[project]/data/
    ```

- Or use the VOSpace client `vcp` from the `vos` python package:

    ```bash
    # to vault VOSpace for long-term access
    vcp largefile.fits vos:[project]/data/
    # to arc file system (and VOSpace) for short-term access
    vcp largefile.fits arc:[project]/data/
    ```


### What software/containers are available?

Containers include general astronomy stacks (AstroPy ecosystem), Jupyter, data science tools, machine learning libraries, full Linux desktops, and specialised astronomy tools (CASA, CARTA, DS9, TOPCAT). You can also build and use custom containers. See the Container Guide at `platform/containers/index.md`.


### Can I install additional software?

- `pip install --user ...` (the `--user` option may not be necessary depending on container) or within environments. Software will be persisted on `/arc`
- Permanent: build a custom container with your required stack (see `platform/containers/index.md`). Software will be persisted on the container.


### Collaboration and sharing

- Share data via project groups and `/arc/projects/[project]/` or in vault VOSPace with appropriate permissions.
- Share container images via the Harbor registry on images.canfar.net
- Share code via Git and group storage; document workflows.

### Troubleshooting slow or failing sessions
- **Resource constraints**: Try flexible mode (default) for faster scheduling, or use fixed mode with fewer cores/less RAM if needed. Consider different times of day when cluster load varies.
- **Variable performance in flexible mode**: This is normal - performance adapts to cluster load. For consistent performance, use fixed mode with specific resource values.
- **Container issues**: Verify name/version; try a maintained baseline image.
- **Account/group issues**: Confirm group membership and active account status.
- **Performance optimization**: Process data in fast scratch (e.g., `/scratch/`), parallelize where appropriate, monitor with `htop`, `df -h`, `iotop`.

### Getting help and community
- Documentation: start at `platform/index.md`.
- Help & Support: `platform/support/index.md` (how to contact support and what to include).
- Community: Discord for Q&A and announcements; workshops and office hours are announced there.

## Session Resources

### Why is my session performance variable?
If you're using flexible mode (the default), performance variation is normal and expected. Your session can use more resources when the cluster has capacity available, but may use fewer resources during peak usage times. This adaptive behavior allows for better overall cluster utilization.

For consistent performance, use fixed mode by specifying exact `--cpu` and `--memory` values (CLI) or `cores` and `ram` parameters (Python API).

## Client

### Can I automate session management with the Python client?
Yes. The Python client supports creating, monitoring, and cleaning up sessions programmatically.

Example:
```python
import time
from canfar import Session

session = Session()
sid = session.launch(name="automated", kind="headless", cmd="python", args=["script.py"])

while session.info(sid)[0]["status"] != "Completed":
    time.sleep(60)

session.logs([sid])
session.destroy([sid])
```

### How do I call the REST API directly?
You can use REST endpoints for jobs and sessions if you prefer low‑level control.

Example:
```python
from canfar.sessions import Session

session = Session()
job_ids = session.create(
    name="automated-analysis",
    image="images.canfar.net/skaha/astroml:latest",
    cores=4,
    ram=16,
    kind="headless",
    cmd="python /arc/projects/[project]/scripts/analyze.py",
)
```

### Authentication options for programs
- X.509 certificates (typical for many users).
- OIDC tokens via SRCNet for advanced and cross‑site workflows. See `cli/authentication-contexts.md` for options and flows.


## CLI


### How do I authenticate?

- Certificates:

    ```bash
    cadc-get-cert -u [user]
    # enter CADC password when prompted
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

## 🔧 Troubleshooting

### Common Platform Issues

#### Sessions won't start or take too long to launch

**Possible causes:**

- High cluster usage during peak hours
- Resource requirements too high
- Container image issues
- Insufficient group permissions

**Solutions:**

- Try flexible mode for faster scheduling
- Reduce CPU/memory requirements
- Use off-peak hours (evenings, weekends)
- Verify container image name and availability
- Check group membership for required projects

#### Can't access files or storage

**Possible causes:**

- Incorrect file paths
- Missing group permissions
- Storage quota exceeded
- Network connectivity issues

**Solutions:**

- Verify file paths: `/arc/home/[user]/` vs `/arc/projects/[project]/`
- Check group membership with project administrators
- Clean up old files to free space
- Use `ls -la` and `getfacl` to check permissions

#### Performance is slow or variable

**In flexible mode (default):**

- Performance varies with cluster load (this is normal)
- More resources available during off-peak hours
- Better overall cluster utilisation

**For consistent performance:**

- Use fixed mode with specific CPU/memory values
- Consider batch jobs for large processing tasks
- Use `/scratch/` storage for temporary files

#### Browser or interface problems

**Symptoms:**

- Interface won't load
- Features don't work properly
- Connection timeouts

**Solutions:**

- Use Chrome or Firefox (recommended browsers)
- Clear browser cache and cookies
- Try incognito/private mode
- Disable ad blockers for canfar.net
- Check network connection stability

### Authentication and Access Issues

#### Certificate problems

**Symptoms:**

- Can't login or authenticate
- "Certificate expired" errors
- CLI commands fail with auth errors

**Solutions:**

```bash
# Renew certificate
cadc-get-cert -u [username]

# Check certificate status
cadc-get-cert --days-valid

# For OIDC authentication
canfar auth login
```

#### Permission denied errors

**Symptoms:**

- Can't access project directories
- File operation failures
- Session creation blocked

**Solutions:**

- Verify group membership with project PI
- Check project access through Science Portal
- Ensure account is active and in good standing
- Contact support if permissions seem incorrect

## 🆘 Getting Help

### When to Use Each Support Channel

#### Use Discord for

- Quick questions with fast community response
- Sharing tips and tricks with other users
- General platform discussions
- Finding collaborators

#### Use GitHub Issues for

- Bug reports with reproducible problems
- Feature requests and suggestions
- Documentation improvements
- Technical discussions

#### Email Support for

- Account access problems
- Resource allocation requests
- Data recovery needs
- Complex technical issues
- Security concerns

### Before Contacting Support

1. **Check this FAQ** for common solutions
2. **Search existing issues** on GitHub
3. **Try basic troubleshooting steps** (restart browser, clear cache)
4. **Gather diagnostic information** using commands in [index.md](index.md#diagnostic-commands)

### What to Include in Support Requests

**Essential information:**

- CANFAR username
- Date/time of issue
- Session type and container used
- Browser and version
- Complete error messages
- Steps to reproduce the problem

**Helpful additional details:**

- Screenshots of error screens
- Session IDs for failed jobs
- File paths for access issues
- What you've already tried

### Response Time Expectations

| Issue Type | Response Time | Examples |
|------------|---------------|----------|
| **Critical** | Same day | System outages, data loss, security |
| **High** | 1-2 business days | Session failures, access problems |
| **Normal** | 2-3 business days | General questions, how-to requests |
| **Low** | 3-5 business days | Feature requests, documentation |

### Community Resources

- **[Discord Community](https://discord.gg/vcCQ8QBvBa)**: Active community chat

Remember: The CANFAR community is here to help! Don't hesitate to ask questions, share your experiences, or contribute solutions that might help other users.
