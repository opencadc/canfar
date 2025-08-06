# 5-Minute Quick Start

!!! success "Goal"
    By the end of this guide, you'll have a Jupyter Notebook running on CANFAR with astronomy tools ready to use.

!!! tip "Prerequisites"
    - A CADC Account (Canadian Astronomy Data Centre) - [Sign up here](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html)
    - Logged into the [CANFAR Science Platform](https://canfar.net) and [Harbor Container Registry](https://images.canfar.net) at least once.
    - Python 3.10+
    - Basic familiarity with Python and Jupyter notebooks

## Installation

<!-- termynal -->
```
> pip install skaha --upgrade
---> 100%
Installed
```

## Authentication

<!-- termynal -->
```
$ skaha auth login
Starting Science Platform Login
Fetched CADC in 0.12s
Fetched SRCnet in 1.15s
Discovery completed in 3.32s (5/18 active)
$ Select a Skaha Server: (Use arrow keys)
   🟢 Canada  SRCnet
   🟢 UK-CAM  SRCnet
   🟢 Swiss   SRCnet
   🟢 Spain   SRCnet
 » 🟢 CANFAR  CADC
$ Selected a Skaha Server: 🟢 CANFAR  CADC
X509 Certificate Authentication
$ Username: username
username@ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca
$ Password: ***********
✓ Saving configuration
Login completed successfully!
```

!!! info "What just happened?"
    - Skaha discovered all available Science Platform servers around the world
    - You selected the CADC CANFAR Server
    - You logged into the Science Platform using your CADC credentials
    - The Science Platform generated a certificate for you valid for 10 days
    - The certificate is Stored in `~/.ssl/cadcproxy.pem`

## Launch Your First Notebook

Lets launch a Jupyter notebook with astronomy tools pre-installed, 

<!-- termynal -->
```
$ skaha create notebook skaha/astroml-notebook:latest
Creating notebook session 'scare-monster'...
Successfully created session 'scare-monster' (ID: tcgle3m3)
```

!!! success "What just happened?"
    - Skaha connected to CANFAR using your certificate
    - Skaha defaulted the container image to `images.canfar.net/skaha/astroml-notebook:latest`
    - A Jupyter notebook was launched with the container image
    - A random name was generated for your session, `scare-monster` in this case
    - The Science Platform allocated resources for your notebook and started it.

## Peek Under the Hood

<!-- termynal -->
```
$ skaha events $(skaha ps -q)
```

!!! success "What just happened?"
    - Skaha connected to CANFAR using your certificate
    - We queried the Science Platform for all running sessions via `skaha ps -q`
    - We fetched the events (actions performed by the Science Platform to start your session) for your session
    - The events show the progress of your session being created

## Check Status

<!-- termynal -->
```
$ skaha ps
                                           Skaha Sessions                                            
                                                                                                     
 SESSION ID NAME          KIND     STATUS  IMAGE                                           CREATED   
 ─────────────────────────────────────────────────────────────────────────────────────────────────── 
 tcgle3m3   scare-monster notebook Running images.canfar.net/skaha/astroml-notebook:latest 2 minutes 
```

!!! success "What just happened?"
    - Skaha connected to CANFAR using your certificate
    - The status of your session was checked
    - The session is in `Running` state, ready to use

## Get Session Information

<!-- termynal -->
```
$ skaha info $(skaha ps -q)
                                         Skaha Session Info for tcgle3m3

  Session ID    zkm7yly7
  Name          alert-connect
  Status        Running
  Type          notebook
  Image         images.canfar.net/skaha/astroml-notebook:latest
  User ID       brars
  Start Time    12 seconds ago
  Expiry Time   3 days and 24.00 hours
  Connect URL   https://workload-uv.canfar.net/session/notebook/redacted
  UID           12345
  GID           12345
  Groups        [54321, 54312, 54123, 51234, 12345]
  App ID        <none>
  CPU Usage     0% of 1 core(s)
  RAM Usage     0% of 2G GB
  GPU Usage     Not Requested
```

!!! success "What just happened?"
    - Skaha connected to CANFAR using your certificate
    - The information for your session was fetched
    - When we created a your session, we never specified a name, cpu or memory, so the default values were used
    - The default values are 1 core, 2GB of RAM, and 4 days of lifetime


## Access Your Notebook

Check the status and get the URL to access your notebook:

<!-- termynal -->
```
$ skaha open $(skaha ps -q)
Opening session tcgle3m3 in a new tab.
```

!!! success "What just happened?"
    - Skaha connected to CANFAR using your certificate
    - `skaha ps -q` returns only the session ID of your session
    - Your browser opened the notebook in a new tab

!!! tip "Pro Tip"
    The notebook usually takes 60-120 seconds to start. You can also check status from the command line:

## Start Analyzing!

Once your notebook is running, click the URL to open it in your browser. You'll have access to:

- **Jupyter Lab** with a full Python environment
- **Pre-installed astronomy libraries**: AstroPy, Matplotlib, SciPy, PyTorch, etc.
- **Persistent storage**: Your work is automatically saved at `/arc/home/username/`
- **Ephemeral storage**: For temporary data staging, use `/scratch/`

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
$ skaha delete $(skaha ps -q)
Confirm deletion of 1 session(s)? [y/n] (n): y
Successfully deleted {'tcgle3m3': True} session(s).
```

## Congratulations!

You now have a fully-equipped astronomy computing environment running in the cloud. No software installation, no environment conflicts, no waiting for local resources.

## Next Steps

=== "⚡ Scale Your Analysis"
    - [Massively Parallel Processing](advanced-examples.md#Massively-Parallel-Processing)

=== "🛠️ Advanced Setup"
    - [Authentication Contexts](authentication-contexts.md)
    - [Session Types Guide](session-types.md)

## Troubleshooting

!!! warning "Common Issues"

    - **Notebook won't start?**
        - Check available resources: `skaha stats`
        - Try a smaller configuration (fewer cores/RAM)
        - Check session status: `skaha ps`
    - **Can't access notebook URL?**
      - Wait 1-2 minutes for full startup
      - Check if you're on a VPN that might block the connection
      - Verify the session is in "Running" status

## Need Help?

- 📖 [Complete Documentation](get-started.md)
- 💬 [Community Support](https://github.com/shinybrar/skaha/discussions)
- 🐛 [Report Issues](bug-reports.md)

---

!!! quote "Success Story"
    "I went from never using clouds to analyzing my furry data in under 10 minutes. The setup was so smooth!" - *Tabby Cat, University of Purr*
