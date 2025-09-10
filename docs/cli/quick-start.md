# 5-Minute Quick Start

!!! success "Goal"
    By the end of this guide, you'll have a Jupyter Notebook Session on CANFAR with astronomy tools ready to use.

!!! tip "Prerequisites"
    - A CADC Account (Canadian Astronomy Data Centre) - [Sign up here](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html)
    - You have at least once logged into the [CANFAR Science Platform](https://canfar.net) and [Harbor Container Registry](https://images.canfar.net).
    - Python 3.10+
    - Basic familiarity with Python and Jupyter notebooks

## Installation

<!-- termynal -->
```
> pip install canfar --upgrade
---> 100%
Installed
```

## Authentication

```bash title='Login to CANFAR Science Platform'
canfar auth login
```

<!-- termynal -->
```
$ canfar auth login
Starting Science Platform Login
Fetched CADC in 0.12s
Fetched SRCnet in 1.15s
Discovery completed in 3.32s (5/18 active)
$ Select a Canfar Server: (Use arrow keys)
   🟢 Canada  SRCnet
   🟢 UK-CAM  SRCnet
   🟢 Swiss   SRCnet
   🟢 Spain   SRCnet
 » 🟢 CANFAR  CADC
$ Selected a Canfar Server: 🟢 CANFAR  CADC
X509 Certificate Authentication
$ Username: username
username@ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca
$ Password: ***********
✓ Saving configuration
Login completed successfully!
```


!!! note "Login Pathways"

    === "CADC Users with Existing `~/.ssl/cadcproxy.pem`"
    
        If you’re using the [CADC CANFAR Science Platform](https://canfar.net) and already have a valid certificate at `~/.ssl/cadcproxy.pem`, the CLI will log in automatically

        ```bash
        Starting Science Platform Login
        ✓ Credentials valid
        ✓ Authenticated with CADC-CANFAR @ https://ws-uv.canfar.net/skaha
        Use --force to re-authenticate.
        ```

    === "SRCnet Users"

        If you are a SRCnet user, you will be required to go through the OpenID Connect login process in your web browser.

        ```bash
        Starting Science Platform Login
        Fetched CADC in 0.13s
        Fetched SRCnet in 1.03s
        Discovery completed in 3.20s (13/19 active)
        ? Select a Canfar Server: 🟢 Canada  SRCnet
        Discovering capabilities for https://src.canfar.net/skaha
        OIDC Authentication for https://src.canfar.net/skaha
        Starting OIDC Device Authentication
        ✓ OIDC Configuration discovered successfully
        ✓ OIDC device registered successfully
        ✓ Follow the link below to authorize:
        ```

```bash title="Force Re-Login"
canfar auth login --force
```

!!! success "What just happened?"
    - `canfar` discovered all available Science Platform servers around the world
    - You selected the `CADC CANFAR Server`
    - You logged into the Science Platform using your CADC credentials
    - The Science Platform generated a certificate for you valid for 30 days
    - The certificate is stored in `~/.ssl/cadcproxy.pem`

## Launch Your First Notebook

Lets launch a Jupyter notebook with astronomy tools pre-installed, 

<!-- termynal -->
```
# Launch a notebook session
$ canfar create notebook skaha/astroml:latest
Successfully created session 'finish-inmate' (ID: d1tsqexh)
```

!!! success "What just happened?"
    - We connected to CANFAR using your certificate
    - The CLI defaulted the container image to `images.canfar.net/skaha/astroml:latest`
    - A Jupyter notebook was launched with the container image in **flexible mode**
    - A random name was generated for your session, `finish-inmate` in this case
    - The Science Platform allocated flexible resources for your notebook and started it

## Peek Under the Hood

<!-- termynal -->
```
# Timeline of events taken to launch the notebook session
$ canfar events $(canfar ps -q)
```

!!! success "What just happened?"
    - We connected to CANFAR using your certificate
    - We queried the Science Platform for all running sessions via `canfar ps -q`
    - We fetched the events (actions performed by the Science Platform to start your session) for your session
    - The events show the progress of your session being created

## Check Status

<!-- termynal -->
```
$ canfar ps
                                                CANFAR Sessions

SESSION ID  NAME          KIND         STATUS    IMAGE                           CREATED
──────────────────────────────────────────────────────────────────────────────────────────
d1tsqexh    finish-inmate notebook     Running   skaha/astroml:latest   7 minutes
```

!!! success "What just happened?"
    - We connected to CANFAR using your certificate
    - The status of your session was checked
    - The session is in `Running` state, ready to use

## Get Session Information

<!-- termynal -->
```
$ canfar info $(canfar ps -q)

  Session ID    d1tsqexh
  Name          finish-inmate
  Status        Running
  Type          notebook
  Image         images.canfar.net/skaha/astroml:latest
  User ID       brars
  Start Time    13 minutes ago
  Expiry Time   3 days and 23.77 hours
  Connect URL   https://connect.to/notebook/here
  UID           123456789
  GID           123456789
  Groups        [12345, 67890]
  App ID        <none>
  CPU Usage     0% of 1 core(s)
  RAM Usage     0% of 2G GB
  GPU Usage     Not Requested
```

!!! success "What just happened?"
    - We connected to CANFAR using your certificate
    - The information for your session was fetched
    - When we created your session, we never specified a name, CPU or memory, so **flexible mode** was used
    - Flexible mode allows your session to adapt its resource usage based on cluster availability
    - The session lifetime defaults to 4 days


## Access Your Notebook

Check the status and get the URL to access your notebook:

<!-- termynal -->
```
$ canfar open $(canfar ps -q)
Opening session tcgle3m3 in a new tab.
```

!!! success "What just happened?"
    - We connected to CANFAR using your certificate
    - `canfar ps -q` returns only the session ID of your session
    - Your browser opened the notebook in a new tab

!!! tip "Pro Tip"
    The notebook usually takes 60-120 seconds to start. You can also check status from the command line:

#### Resource Allocation Modes

CANFAR Science Platform supports two resource allocation modes, see [platform concepts](../platform/concepts.md#resource-allocation-modes) for more information.


## Start Analyzing!

Once your notebook is running, click the URL to open it in your browser. You'll have access to:

- **Jupyter Lab** with a full Python environment
- **Pre-installed astronomy libraries**: AstroPy, Matplotlib, SciPy, PyTorch, etc.
- **Storages**
    - **Persistent**: Your work is automatically saved at `/arc/home/username/`
    - **Project**: Large datasets shared within your project at `/arc/projects/name`
    - **Ephemeral**: For temporary data staging, use `/scratch/`

!!! example "Try This First"
    In JupyterLab, open a new Notebook and run the following code to verify your environment:

    ```python
    import astropy
    from astropy.io import fits
    import matplotlib
    import numpy as np

    print(f"AstroPy version: {astropy.__version__}")
    print(f"Matplotlib version: {matplotlib.__version__}")
    print(f"Numpy version: {np.__version__}")
    print(f"GPU available: {torch.cuda.is_available()}")
    print("Ready for astronomy!")
    ```

## Clean Up

When you're done, clean up your session to free up resources for others:

<!-- termynal -->
```
$ canfar delete $(canfar ps -q)
Confirm deletion of 1 session(s)? [y/n] (n): y
Successfully deleted {'tcgle3m3': True} session(s).
```

## Congratulations!

You now have a fully-equipped astronomy computing environment running in the cloud. No software installation, no environment conflicts, no waiting for local resources.


## Troubleshooting

!!! warning "Common Issues"

    - **Notebook won't start?**
        - Check available resources: `canfar stats`
        - Try flexible mode (default) for faster scheduling
        - If using fixed mode, try smaller resource values (fewer cores/RAM)
        - Check session status: `canfar ps`
    - **Can't access notebook URL?**
      - Wait 1-2 minutes for full startup
      - Check if you're on a VPN that might block the connection
      - Verify the session is in "Running" status
    - **Variable performance in flexible mode?**
      - This is normal - performance adapts to cluster load
      - For consistent performance, use fixed mode with specific `--cpu` and `--memory` values
