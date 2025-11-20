# CANFAR Science Platform 2025.1

!!! success "CANFAR Science Platform 2025.1"

    **Dear CANFAR Community,**

    We are pleased to announce a major milestone for the CANFAR Science Platform: On September 9, 2025, we completed a transition from a beta system, initially released in 2021, to our first production release, CANFAR Science Platoform 2025.1, marking the beginning of an official production release cycle.

    This latest version is ready for use on www.canfar.net, and is also available for deployments to pick up across SRCNet.

    !!! danger ""
        
        If you use scripts to launch sessions on the science platform via the now deprecated [skaha python package](https://github.com/shinybrar/skaha) or with curl, please switch to the new [CANFAR Python Client or CLI](client/home.md). If you access the API directly, please switch the reference to `skaha/v0` to `skaha/v1` as soon as possible.

    ### ✨ Highlights
    - [**New & Improved** User Documentation Hub](index.md)
    - **Official Release of the CANFAR Python Client & CLI** — see [clients docs](client/home.md)
    - **Smart Session Launching** — choose between **flexible** (auto-scaling) and **fixed** modes
    - **Science Portal UI Improvements** — added display for home directory & storage quota usage
    - **CARTA 5.0**: latest radio astronomy visualization tool ([August 2025 Release](https://docs.google.com/document/d/1kBtYjclOn5bxlvkV5a588DtUKy3UEqPXL78IiTVAMUk/edit?tab=t.0#heading=h.9m3bw7vn40ea))
    - **Firefly**: IVOA-compliant catalog browsing and visualization platform

    ### 📝 Changes & Deprecations
    - **Breaking Changes**:
        - For API users, `headless` sessions no longer require the `type` parameter
        - For Python Client & CLI users, `headless` sessions no longer require the `kind` parameter and the `headless` session `kind` will be deprecated in a future release.
        - `Succeeded` status is now `Completed` for all session types, e.g. when performing a `session.info()` query.
    - **Skaha API `v1` Released** — [`v0`](https://ws-uv.canfar.net/skaha/v0) API will be sunset with the next major release. Portal users are unaffected; API users should plan to migrate to `v1` as soon as possible.
    - **Container Image Labels** are no longer required in the [Harbor Image Registry](https://images.canfar.net/). They are only used to populate dropdown menu options in the Science Portal UI.
    - **Session Types** — launching via API, omit the `type` parameter for headless mode; interactive sessions require the `type` parameter.
    - **Status Changes** — Job status `Succeeded` is now `Completed` for all session types.


    ### 🐛 Fixes
    - **Resource Monitoring** — RAM and CPU usage for sessions now display correctly in the Science Portal UI.

    ### ⚙️ Technical Changes
    - CANFAR deployment requires Kubernetes v1.29 or later
    - **Kueue Scheduling** — optional advanced job scheduling system that can be enabled per namespace to reduce cluster pressure and provide queue management.
    - **Monitoring Fixes** — Skaha API now uses the the Job API instead of the Pod API internally to provide more accurate resource usage information.
    - **Flexible** sessions use the `Burstable` Kubernetes Quality of Service (QoS) class instead of `Guaranteed`, which provides better resource efficiency on the cluster. Currently, *flexible* sessions can grow up to 8 cores and 32GB of RAM.
    - Internal API's have been updated to use the `Job` API instead of the `Pod` API. This provides better resource monitoring and usage information.
   

    ### 📦 Deployment Notes

    - Use the offically supported helm charts in the [opencadc/deployments](https://github.com/opencadc/deployments/tree/main/helm/applications/skaha) for CANFAR 2025.1 deployments.
    - To test, profile and setup the Kueue scheduling system, see the [deployment guide](https://github.com/opencadc/deployments/tree/main/configs/kueue) for detailed instructions.

    #### Python Client & CLI 
    
    | Component | Version |
    |---------|--------------|
    | canfar | [v1.0.2](https://pypi.org/project/canfar/) |
    
    #### Helm Charts & Container Images
        
    | Component | Helm Chart Version | Container Image |
    |-----------|-------------------|-----------------|
    | base | 0.4.0 | N/A |
    | cavern | 0.7.0 | images.opencadc.org/platform/cavern:0.9.0 |
    | skaha | 1.0.3 | images.opencadc.org/platform/skaha:1.0.2 |
    | posix-mapper | 0.4.4 | images.opencadc.org/platform/posix-mapper:0.3.2 |
    | science-portal | 1.0.0 | images.opencadc.org/platform/science-portal:1.0.0 |
    | storage-ui | 0.6.0 | images.opencadc.org/client/storage-ui:1.3.0 |

    ### 💬 Contact & Support

    For any questions about this release, or for information relating to CANFAR issues or deployment support, head over to the [CANFAR Discord Server](https://discord.gg/vcCQ8QBvBa) or please contact us at [support@canfar.net](mailto:support@canfar.net).

    <br>
    <div style="text-align: center;">
    Built with :heart:{.heart} at CADC
    </div>
