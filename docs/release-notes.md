# CANFAR Science Platform 2025.1

!!! tip "CANFAR Science Platform 2025.1"

    The CANFAR Team is proud to announce the first formal release of the CANFAR Science Platform.
    
    **Status: Released**

    ### ✨ Highlights
    - [**New & Improved** User Documentation Hub](https://www.opencadc.org/canfar/latest/)
    - **Offcial Release of the CANFAR Python Client & CLI** — see [clients docs for more details.](client/home.md)
    - **Smart Session Launching** — **Flexible** (auto-scales) and **Fixed** modes
    - **Portal Enhancements** — home directory usage & quota information display
    - **New Science Use Cases** — [CARTA 5.0](platform/guides/interactive-sessions/launch-carta.md) and [Firefly](platform/guides/interactive-sessions/launch-firefly.md) support
    - **Batch Job Scheduling** is now generally availaible for all users via the [CANFAR Python Client](client/home.md) and [CLI](cli/quick-start.md).

    ### 📝 Changes & Deprecations
    - **Skaha API has been upgraded to `v1`**. The [`v0`](https://ws-uv.canfar.net/skaha/v0) API is scheduled to be sunset with the release of **CSP 2026.1**. Portal users are unaffected; API users should plan to move to v1.
    - **Container Image Labels** are no longer required in the [Harbor Image Registry](https://images.canfar.net/). They are only used to populate dropdown menu options in the Science Portal UI for public images.
    - **`headless`** mode is the default session behavior, use the `kind` flag in the client and CLI to override this.
    

    ### 🐛 Fixes
    - **Resource Monitoring** — RAM and CPU usage for sessions/headless jobs are shown again in the portal.

    ### ⚙️ For Deployers
    - **Kueue Scheduling**: Optional advanced job scheduling system available for deployment to reduce cluster pressure and provide queue management. See [deployment configuration](https://github.com/opencadc/deployments/tree/main/configs/kueue) for setup instructions.

    ---

    ## 🔍 Detailed Technical Information

    ### System Architecture Changes
    - **Kubernetes Upgrade**: Cluster upgraded to **Kubernetes 1.28** for improved performance and security
    - **Queue Management**: Internal scheduler now fronted by Kueue system to alleviate cluster pressure
    - **Resource Allocation**: Smart session launching with **Flexible** (auto-scaling) and **Fixed** modes for better cluster efficiency

    ### API Evolution
    - **Skaha API v1**: New endpoint at `https://ws-uv.canfar.net/skaha/`
    - **Backward Compatibility**: v0 API remains available during transition period (sunset with CSP 2026.1)
    - **Session Parameters**: Interactive sessions now require `type` parameter; headless jobs should omit it

    ### Container & Image Management  
    - **Harbor Labels**: No longer required for session launching (only for Science Portal UI dropdown population)
    - **Headless Mode**: Now default session behavior - any image can run headless without special labels
    - **Science Containers**: Curated containers available in [skaha project](https://images.canfar.net/) on Science Portal

    ### Enhanced User Experience
    - **Documentation Hub**: Complete overhaul at [canfar.net/docs](https://www.canfar.net/docs)
    - **Portal Improvements**: Home directory usage and quota display in top-right corner
    - **Batch Workflows**: Programmatic access via Python Client and CLI for workflow automation
    - **Resource Monitoring**: Restored real-time RAM and CPU usage display for all sessions

    ### Scientific Computing Tools
    - **CARTA 5.0**: Latest radio astronomy visualization tool (August 2025 release)
    - **Firefly**: IVOA-compliant catalog browsing and visualization platform
    - **Multi-wavelength Support**: Enhanced containers for diverse astronomical workflows

    ### Future Roadmap
    - Queue status information will be displayed in Science Portal (upcoming release)
    - Enhanced resource quotas and budgeting system under development
    - Continued optimization of cluster resource utilization