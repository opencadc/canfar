---
hide:
  - navigation
  - toc
---

<h1>CANFAR Science Platform </h1>
    
!!! note ""
    
    <center>
    <h3>
    **Canadian Advanced Network for Astronomical Research is a scalable, cloud-native workspace for astronomy research.**
 
    *Spin up JupyterLab, submit batch jobs, and collaborate in shared project spaces. <br> The CANFAR Science Platform gives researchers the tools they need with minimal setup.*
    </h3>
    </center>
    
!!! success ""

    <h4>Discover what the CANFAR Science Platform can do for you, your team, and your research group.</h4>

    <h3>

    <div class="grid cards" markdown>

    - [:material-monitor: __Interactive Sessions__ <small>e.g. JupyterLab</small>](platform/guides/interactive-sessions/index.md)
    - [:material-lightning-bolt: __Batch Processing__ <small>for large-scale analysis</small>](platform/batch-jobs.md)
    - [:material-floppy-variant: __Shared Storage__ <small>for collaborative datasets</small>](platform/guides/storage/index.md)
    - [:material-docker: __Software Containers__ <small>with astronomy tools</small>](platform/containers.md)
    - [:fontawesome-solid-people-roof: __Collaboration Tools__ <small>with group permissions</small>](platform/accounts.md)
    - [:material-wrench: __Expert Support__ <small>for research workflows</small>](platform/help.md)
    - [:simple-python: __Python API__ <small>for access and automation</small>](client/home.md)
    - [:simple-gnubash: __CLI__ <small>for terminal users</small>](cli/quick-start.md)
    - [:simple-doi: __Publications__ <small>of DataCite DOIs</small>](platform/legacy/publication.md)
    - [:simple-wpexplorer: and much more...](platform/guides/index.md)

    </div>
    
    </h3>

!!! info "📢 Release Notes"

    ??? info "🚀 CanfarSP 2025.1 — September 9, 2025"
        **The first formal release of the CANFAR Science Platform** 🎉  
        Status: Scheduled • Version: **CANFAR-SP 2025.1**

        ### ✨ Summary & Highlights
        - **User Docs Overhaul** — new site at <https://www.opencadc.org/canfar/latest/>
        - **Official Python Client & CLI** — first public release
        - **Smart Session Launching** — **Flexible** (auto-scales) and **Fixed** modes
        - **Portal Enhancements** — home directory usage & quota in the top-right
        - **New Science Containers** — CARTA 5.0, Firefly (IVOA-compliant)

        ### 🆕 New & Improved
        - **API** — **Skaha API v1** introduced: `https://ws-uv.canfar.net/skaha/`  
          `v0` will remain available during a transition period (sunset date TBA).  
          Portal users are unaffected; API callers should plan to move to v1.
        - **Images & Labels** — labels not required to run headless jobs;  
          interactive sessions must provide a `type` parameter.
        - **Scheduling** — internal scheduling fronted by **Kueue** to reduce cluster pressure.
        - **Platform** — Kubernetes upgraded to **1.28**.

        ### 🐛 Fixes
        - **Resource Monitoring** — RAM and CPU usage for sessions/headless jobs are shown again in the portal.

        ### 🔄 Upgrade Notes
        - **API callers**: plan migration to **Skaha v1**; v0 deprecation date will be announced.
        - **CLI**: if you used the beta "skaha" CLI, switch to the official **canfar** CLI.
        - **Launch parameters**: interactive sessions require `type`; headless jobs should omit `type`.

        ### 🔗 Links
        - **Science Portal** — <https://www.opencadc.org/canfar/latest/>
        - **User Documentation** — <https://www.opencadc.org/canfar/latest/platform/home/>
        - **API v1** — `https://ws-uv.canfar.net/skaha/`
        - **GitHub (canfar)** — <https://github.com/opencadc/canfar>

!!! quote ""

    <font size="3">
    ##### If you use CANFAR, add an acknowledgement to your papers, theses, and other research outputs.
    </font>

    <span style="font-family: 'Roboto Mono', monospace; font-size: 12px; font-style: italic;">
    The authors acknowledge the use of the Canadian Advanced Network for Astronomy Research (CANFAR) Science Platform operated by the Canadian Astronomy Data Center (CADC) and the Digital Research Alliance of Canada (DRAC), with support from the National Research Council of Canada (NRC), the Canadian Space Agency (CSA), CANARIE, and the Canadian Foundation for Innovation (CFI).
    </span>

###### Built on **[IVOA standards](https://www.ivoa.net/documents/)** & **[F.A.I.R. principles](https://www.go-fair.org/fair-principles/)**