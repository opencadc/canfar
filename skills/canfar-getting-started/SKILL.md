---
name: canfar-getting-started
description: >
  Getting started on CANFAR: CADC or SRCNet account, request access, join a project
  via PI/group, Science Portal first Session, persistence, fair use, and
  acknowledgement text.
  Use for new users, access request, how to begin, who can use CANFAR, cost.
---
# Getting started on CANFAR

Start with the user's deployment and role. A student joining an existing project
usually needs an identity plus group membership; a PI requesting storage or large
compute also needs a project/allocation conversation.

## Who can use the CADC deployment

- CANFAR access is provided for astronomical research under site policy and
  allocation limits; it is not a general-purpose free cloud.
- CADC serves Canadian astronomers and collaborators. SRCNet nodes have their own
  eligibility and support paths.
- Larger needs: [Alliance Resource Allocation](https://docs.alliancecan.ca/)

## Deployment note

CANFAR is open source and sites configure their own Science Portal, identity,
storage, Container Registry, and limits. Examples below use **CADC**
(`www.canfar.net`). A current CLI can discover CADC and SRCNet Servers:

```bash
pip install canfar
canfar login srcnet
canfar auth show
```

## Access path (CADC)

### 1. CADC account

Request at: [CADC account request](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html)

### 2. CANFAR platform access

**Option A — email** (typical 1–2 business days):

Email `support@canfar.net` with CADC username and brief research description.

**Option B — join existing team:**

Ask your PI to add you to the project's **CADC group** (see `canfar-groups`).

### 3. First Session

1. Open the Science Portal and log in (CADC:
   [canfar.net/science-portal](https://www.canfar.net/science-portal/)).
2. Choose an available Session kind and Container Image. For a first visit,
   Notebook plus a general astronomy image is usually the least surprising.
3. Find the site's persistent personal/project mount (CADC: `/arc/home` and
   `/arc/projects`; many Skaha sites use `/cavern`).
4. Use `/scratch` only for temporary processing and copy results to persistent
   storage before deleting or letting the Session expire.

```bash
canfar login cadc
canfar image ls --kind notebook
canfar create notebook skaha/astroml:latest --name first-test
canfar ps
```

## Key concepts (learn next)

| Topic | Skill |
| --- | --- |
| Storage tiers | `canfar-storage` |
| Teams & groups | `canfar-groups` |
| Session types | `canfar-sessions` |
| Auth / SRCNet | `canfar-auth` |

## Acknowledgement (papers/theses)

> The authors acknowledge the use of the Canadian Advanced Network for Astronomy Research (CANFAR) Science Platform operated by the Canadian Astronomy Data Centre (CADC) and the Digital Research Alliance of Canada…

Full text: [CANFAR home](https://www.opencadc.org/canfar/latest/)

## Help

- [Getting started guide](https://www.opencadc.org/canfar/latest/platform/get-started/)
- [FAQ](https://www.opencadc.org/canfar/latest/platform/support/faq/)
- CADC: `support@canfar.net` · deployment Discord (see your portal)
