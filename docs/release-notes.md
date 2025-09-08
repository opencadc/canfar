# CANFAR Science Platform 2025.1

!!! tip "CANFAR Science Platform 2025.1"

    The CANFAR Team is proud to announce the first formal release of the CANFAR Science Platform.
    
    **Status: Released**

    ### ✨ Highlights
    - [**New & Improved** User Documentation Hub](https://www.opencadc.org/canfar/latest/)
    - **Offcial Release of the CANFAR Python Client & CLI** — see [clients docs for more details.](client/home.md)
    - **Smart Session Launching** — **Flexible** (auto-scales) and **Fixed** modes
    - **Portal Enhancements** — home directory usage & quota information display
    - **New Science Use Cases** — CARTA 5.0 and Firefly support
    - **Batch Job Scheduling** is now generally availaible for all users via the [CANFAR Python Client](client/home.md) and [CLI](cli/quick-start.md).

    ### 📝 Changes & Deprecations
    - **Skaha API has been upgraded to `v1`**. The [`v0`](https://ws-uv.canfar.net/skaha/v0) API is scheduled to be sunset with the release of **CSP 2026.1**. Portal users are unaffected; API users should plan to move to v1.
    - **Container Image Labels** are no longer required in the [Harbor Image Registry](https://images.canfar.net/). They are only used to populate dropdown menu options in the Science Portal UI for public images.
    - **`headless`** mode is the default session behavior, use the `kind` flag in the client and CLI to override this.
    

    ### 🐛 Fixes
    - **Resource Monitoring** — RAM and CPU usage for sessions/headless jobs are shown again in the portal.