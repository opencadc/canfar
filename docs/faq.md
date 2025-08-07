# Frequently Asked Questions

Common questions and answers about using Skaha with the CANFAR Science Platform.

## Getting Started

### What is the CANFAR Science Platform?

The CANFAR Science Platform is a national cloud computing infrastructure for astronomy research. It allows you to launch Jupyter notebooks, desktop applications, and batch processing jobs in the cloud.

### Do I need a CADC account?

Yes, you need a Canadian Astronomy Data Centre (CADC) account to use the Science Platform. You can [request an account here](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html).

### How much does it cost?

The CANFAR Science Platform access is free for Canadian astronomers and their international collaborators. Resource usage is subject to fair-use policies and allocation limits. If you require significantly more resources, you can request additional resources through the Digital Research Alliance of Canada (DRAC) [Resource Allocation Competition](https://alliancecan.ca/en/services/advanced-research-computing/accessing-resources/resource-allocation-competition) and they can be used on the CANFAR Science Platform.

### What's the difference between the Science Platform and other cloud platforms?

The Science Platform is specifically designed for astronomy research with:
- Hundreds of community contributed and staff maintained container images
- Support for availaible astronomy software (Firefly, CARTA, etc.)
- Direct access to 6PB+ of CADC data archives
- No setup or configuration required
- Co-located with with Canadian Astronomy Infrastructure, e.g. YouCat, CAOM, DOI, Vault Storage, etc.

## Authentication

### How do I get authenticated?

Use X.509 certificates (recommended for most users):

```bash
cadc-get-cert -u your-username
```
or 
```
skaha auth login
```
```bash title="Choose CANFAR CADC Server"
Starting Science Platform Login
Fetched CADC in 0.14s
Fetched SRCnet in 1.09s
Discovery completed in 4.62s (6/18 active)
? Select a Skaha Server: (Use arrow keys)
   🟢 Canada  SRCnet
   🟢 UK-CAM  SRCnet
   🟢 Swiss   SRCnet
   🟢 Italy   SRCnet
 » 🟢 CANFAR  CADC
```

Certificates are valid for 10 days and need to be renewed regularly.

### Can I use OIDC tokens instead of certificates?

Yes, OIDC (OpenID Connect) tokens are supported for advanced users and programmatic access accessing the Science Platform through the Square Kilometer Array (SKA) Science Regional Network (SRCNet). To setup OIDC authentication, use

```
skaha auth login
```
```bash title="Choose SRCNet Server"
Starting Science Platform Login
Fetched CADC in 0.14s
Fetched SRCnet in 1.09s
Discovery completed in 4.62s (6/18 active)
? Select a Skaha Server: (Use arrow keys)
 » 🟢 Canada  SRCnet
   🟢 UK-CAM  SRCnet
   🟢 Swiss   SRCnet
   🟢 Italy   SRCnet
   🟢 CANFAR  CADC
```

## Sessions and Resources

### What session types are available?

- **Notebook**: Interactive Jupyter Lab environment
- **Desktop**: Full Linux desktop with GUI applications
- **Headless**: Command-line only for batch processing
- **Firefly**: Advanced image visualization tool
- **CARTA**: Image visualization tool

See the [Session Types Guide](session-types.md) for detailed information.

### How much CPU and RAM can I request?

Limits vary based on the underlying hardware and current load on the system. You can see the current statistics with,

```
skaha stats
```

### How long do sessions run?

Sessions run until,
  - You destroy the session.
  - The session reaches a natural termination point (e.g. batch job completes).
  - The session exceeds the maximum runtime (typically 30 days).

In very rare cases, sessions may be terminated early if,
- Resources are needed for higher-priority work
- System maintenance is required
- Fair-use policies are misused

### Why is my session stuck in "Pending"?

Common causes:
- Insufficient resources available to fulfill request
- Image not found or inaccessible
- Resource quota exceeded
- System maintenance

You can check the events for a session to see the pending reason with,
```
skaha events <session-id>
```

## Images and Software

### Can I use my own container images?

Yes, you can use:
- **Public images**: Any publicly accessible container
- **Private images**: From CANFAR Harbor registry (requires credentials)
- **Custom images**: Build and push to CANFAR Harbor

## Data Access

### How do I access my data?

Your data is available in several locations:
- **Home directory**: `/arc/home/username/` (persistent, slow storage)
- **Shared data**: `/arc/projects/project-name/` (project-specific storage)
- **Scratch space**: `/scratch/` (temporary, high-performance)

## Performance and Optimization

### Can I run multiple sessions simultaneously?

Yes, you can run multiple sessions simultaneously with upto 3 Notebook sessions, 1 Desktop session, and `unlimited` Headless session.

## Troubleshooting

### I can't connect to my session URL. Help!

Troubleshooting steps:
1. **Wait for "Running" status**: Check `skaha ps`
2. **Check VPN**: Some VPNs block CANFAR connections
3. **Try different browser**: Clear cache or use incognito mode

### How do I get help with errors?

1. **Check this FAQ**
2. **Search GitHub issues**: [github.com/shinybrar/skaha/issues](https://github.com/shinybrar/skaha/issues)
3. **Ask the Community**: [Discord Server](https://discord.gg/vcCQ8QBvBa)

## Advanced Usage

### Can I automate session management?

Yes, Skaha is designed for automation:
```python
# Automated workflow
session = Session()
session_id = session.create(name="automated", kind="headless", cmd="python", args=["script.py"])

# Monitor until completion
while session.info(session_id)[0]['status'] != 'Completed':
    time.sleep(60)

# Get results and cleanup
session.logs([session_id])
session.destroy([session_id])
```

## Policies and Limits

### What are the fair-use policies?

- **Resource sharing**: Don't monopolize resources unnecessarily
- **Session cleanup**: Destroy sessions when finished
- **Appropriate use**: Use for astronomy research and education
- **Data management**: Don't store unnecessary data long-term

### Are there usage quotas?

Yes, quotas vary by user and allocation, but generally there are quotas on:
- **Concurrent sessions**: Hard limits on notebooks, desktop, firefly, and carta and no limit on headless
- **Total resources**: No hard limits, but fair-use applies
- **Storage**: Hard limits on `/arc` and `/arc/projects`
- **Time limits**: No hard limits, but fair-use applies

## Getting Help

### How do I report bugs or request features?

- **Bugs**: [Report on GitHub](https://github.com/shinybrar/skaha/issues)
- **Feature requests**: [GitHub Discussions](https://github.com/shinybrar/skaha/discussions)
- **Security issues**: [Security reporting](security.md)

### Is there a user community?

Yes! Join the community:
- **GitHub Discussions**: Ask questions and share experiences
- **CANFAR Forums**: Official CANFAR community forums
- **Workshops**: Regular training workshops and webinars
- **Documentation**: Contribute to documentation improvements

---

!!! question "Didn't find your answer?"
    Check the [troubleshooting guide](troubleshooting.md) or ask the community on [GitHub Discussions](https://github.com/shinybrar/skaha/discussions).
