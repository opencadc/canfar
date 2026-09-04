# OpenCADC CANFAR ecosystem and deployment map

Read this reference when a user asks which component implements a capability,
why two deployments behave differently, or where to verify an architecture claim.
For ordinary user questions, keep the answer at the Portal, CLI, or Python API
level and do not recite this map.

## Repository ownership

| OpenCADC repository | User-visible responsibility | Treat as authoritative for |
| --- | --- | --- |
| `opencadc/canfar` | User documentation, `canfar` CLI, sync/async Python clients, Authentication, Server Selection, Storage Identifiers | Current command syntax, Python API, domain vocabulary, client discovery and validation |
| `opencadc/science-platform` | Skaha Session/image REST service, Kubernetes Job templates, Metrics, current Skaha Helm chart | Session kinds, lifecycle enforcement, image allow-listing, probes, resource and mount templates, chart defaults |
| `opencadc/science-portal` | Current Next.js Science Portal and browser-facing backend | Current web Session workflow, browser auth modes, deployment-configured service links and endpoints |
| `opencadc/deployments` | Deployable supporting Helm charts and operational guidance | Cavern, Storage UI, Access, POSIX Mapper, Registry, SSHD, Kueue, and integration patterns; archived Skaha/Portal charts are historical |
| `opencadc/vos` | Cavern VOSpace server and Java VOSpace client | VOSpace-over-POSIX implementation and service behavior |
| `opencadc/vostools` | Python `vos` package and legacy commands such as `vcp`, `vls`, `vsync`, and `vchmod` | Exact legacy VOSpace command syntax and limits |
| `opencadc/cadctools` | CADC authentication utilities, archive data access, TAP clients | `cadc-get-cert`, `cadcget`, `cadctap`, certificate and archive client behavior |
| `opencadc/canfar-library` | Scientist-first, manifest-driven container build/publish tooling | Optional `library` CLI workflow; check its release status before recommending it as installed |
| `opencadc/canfar-portal` | Public CANFAR website and links to services | Landing-page/service navigation; it is not the current Science Portal Session UI |

## Evidence order

The code is the behavioral source of truth. Use the narrowest evidence that
answers the question:

1. **Current implementation and tests:** `opencadc/canfar` for CLI/Python
   behavior, `opencadc/science-platform` for Skaha/Job behavior,
   `opencadc/science-portal` for the browser workflow, and the relevant VOS/CADC
   package for storage or archive behavior.
2. **Deployment composition:** current Helm templates plus the operator's
   site-specific values. Templates define supported knobs; deployed values
   determine configured paths, endpoints, limits, and optional services.
3. **Live observation:** Portal values, `canfar auth show`, `canfar server ls`,
   `canfar image ls`, `canfar info`, `canfar stats`, and Session events confirm
   what that deployment currently exposes.
4. **Legacy compatibility:** `opencadc/vostools`, older `cadctools`, and archived
   charts only when the user is actually using those interfaces.
5. **Public documentation:** use as a user-facing orientation/link only after
   checking it against the code; it can lag the implementation.

Never infer a live quota, path, registry, expiry, or authorization policy from a
default values file. Never infer current Skaha or Portal behavior from an archived
chart in `opencadc/deployments`.

## Architecture seams that matter to users

- **Authentication is not Server Selection.** Logging in establishes an
  Authentication Record; Server Selection chooses where new requests go.
- **A Server can expose multiple VOSpace Services.** Address them by discovered
  Storage Identifier (`arc:`, `vault:`, `cavern:`, or a site-defined name).
- **Identity, platform authorization, project allocation, POSIX permissions,
  VOSpace ACLs, and registry roles are separate checks.** A user can pass one and
  fail another.
- **Cavern is an implementation; ARC is a CADC deployment name.** Both can expose
  a VOSpace service backed by shared POSIX storage, but paths and identifiers are
  deployment data.
- **Science Portal and Skaha are different layers.** Portal is the web client;
  Skaha owns Session/image service behavior.
- **Charts are configurable.** Kueue, CVMFS, GPU pools, registry hosts, storage
  mounts, and authorization modes may be absent or different at another site.
