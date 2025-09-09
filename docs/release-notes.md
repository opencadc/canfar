# CANFAR Science Platform 2025.1

!!! tip "CANFAR Science Platform 2025.1"

    The CANFAR Team is proud to announce the first formal release of the CANFAR Science Platform.
    
    **Status: Released**

    ### ✨ Highlights
    - [**New & Improved** User Documentation Hub](https://www.opencadc.org/canfar/latest/)
    - **Official Release of the CANFAR Python Client & CLI** — see [clients docs for more details.](client/home.md)
    - **Smart Session Launching** — **Flexible** (auto-scales) and **Fixed** modes
    - **Portal Enhancements** — home directory usage & quota information display
    - **CARTA 5.0**: Latest radio astronomy visualization tool ([August 2025 Release](https://docs.google.com/document/d/1kBtYjclOn5bxlvkV5a588DtUKy3UEqPXL78IiTVAMUk/edit?tab=t.0#heading=h.9m3bw7vn40ea))
    - **Firefly**: IVOA-compliant catalog browsing and visualization platform

    ### 📝 Changes & Deprecations
    - **Skaha API has been upgraded to `v1`**. The [`v0`](https://ws-uv.canfar.net/skaha/v0) API will be sunset at a date TBA (to be announced). Portal users are unaffected; API users should plan to move to v1.
    - **Container Image Labels** are no longer required in the [Harbor Image Registry](https://images.canfar.net/). They are only used to populate dropdown menu options in the Science Portal UI for public images.
    - **Session Types**: When launching via API, omit the `type` parameter for headless mode; interactive sessions require the `type` parameter.
    

    ### 🐛 Fixes
    - **Resource Monitoring** — RAM and CPU usage for sessions/headless jobs are shown again in the portal.  

    ### Technical Notes

    #### System Architecture Changes
    - CANFAR now requires Kubernetes v1.29 or later
    - **Kueue Scheduling**: Optional advanced job scheduling system that can be enabled per namespace to reduce cluster pressure and provide queue management.
    - The resource monitoring fixes for the science portal now query the the Job API instead of the Pod API internally.
    - *Flexible* sessions now use the `Burstable` Kubernetes Quality of Service (QoS) class instead of `Garanteed`, which provides better resource efficiency on the cluster. Currently, `flexible` sessions can grow upto 8 cores and 32GB of RAM.

    #### API Evolution
    - With the release of `v1` of the Skaha API, the Python client has been updated to support the new API. The `v0` API will be sunset with release `2026.1`. This is a **breaking change** for API users, as the `kind` parameter can now be omitted for headless jobs.
    - **Harbor Labels** are no longer required for session launching and only used to populate dropdown menu options in the Science Portal UI.

    #### Deployment
    - For admins who wish to deploy CANFAR 2025.1, please see use the offically supported helm charts in the [opencadc/deployments](https://github.com/opencadc/deployments/tree/main/helm/applications/skaha) repository.
    - To test, profile and install the Kueue scheduling system, see the [deployment configuration](https://github.com/opencadc/deployments/tree/main/configs/kueue) for detailed instructions.