# CANFAR Science Platform 2025.1

!!! tip "CANFAR Science Platform 2025.1"

    The CANFAR Team is proud to announce the first formal release of the CANFAR Science Platform.
    
    **Status: Released**

    ### ✨ Highlights
    - [**New & Improved** User Documentation Hub](index.md)
    - **Official Release of the CANFAR Python Client & CLI** — see [clients docs](client/home.md)
    - **Smart Session Launching** — choose between *flexible** (auto-scaleing) and *fixed** modes
    - **Portal Enhancements** — home directory & quota display
    - **CARTA 5.0**: latest radio astronomy visualization tool ([August 2025 Release](https://docs.google.com/document/d/1kBtYjclOn5bxlvkV5a588DtUKy3UEqPXL78IiTVAMUk/edit?tab=t.0#heading=h.9m3bw7vn40ea))
    - **Firefly**: IVOA-compliant catalog browsing and visualization platform

    ### 📝 Changes & Deprecations
    - **Skaha API `v1` Released** — [`v0`](https://ws-uv.canfar.net/skaha/v0) API will be sunset with `2026.1` release. Portal users are unaffected; API users should plan to migrate to v1.
    - **Container Image Labels** — no longer required in the [Harbor Image Registry](https://images.canfar.net/). They are only used to populate dropdown menu options in the Science Portal UI.
    - **Session Types** — launching via API, omit the `type` parameter for headless mode; interactive sessions require the `type` parameter.
    

    ### 🐛 Fixes
    - **Resource Monitoring** — RAM and CPU usage for sessions now display correctly in the Science Portal UI.

    ### Technical Notes

    #### System Architecture Changes
    - CANFAR deployment requires Kubernetes v1.29 or later
    - **Kueue Scheduling** — optional advanced job scheduling system that can be enabled per namespace to reduce cluster pressure and provide queue management.
    - **Monitoring Fixes** — Skaha API now uses the the Job API instead of the Pod API internally to provide more accurate resource usage information.
    - *Flexible* sessions now use the `Burstable` Kubernetes Quality of Service (QoS) class instead of `Guaranteed`, which provides better resource efficiency on the cluster. Currently, `flexible` sessions can grow upto 8 cores and 32GB of RAM.

    #### API Evolution
    - Skaha API v1 — supported in the updated Python Client & CLI. 
      - **Breaking change**:
        - For API users, `headless` sessions no longer require the `type` parameter
        - For Python Client & CLI users, `headless` sessions no longer require the `kind` parameter and the `headless` session `kind` will be deprecated in a future release.
    - **Harbor Labels** are no longer required for session launching and only used to populate dropdown menu options in the Science Portal UI and only for publicly visible container images.

    #### Deployment
    - Use the offically supported helm charts in the [opencadc/deployments](https://github.com/opencadc/deployments/tree/main/helm/applications/skaha) for CANFAR 2025.1 deployments.
    - To test, profile and setup the Kueue scheduling system, see the [deployment guide](https://github.com/opencadc/deployments/tree/main/configs/kueue) for detailed instructions.