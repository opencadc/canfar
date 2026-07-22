# CANFAR

CANFAR is a science platform for authenticated astronomical compute, Container Images, and user Sessions. This glossary names domain concepts only; implementation details live in code and issue-tracker records.

## Language

**CANFAR Science Platform**:
Cloud-native environment for astronomical research workflows.
_Avoid_: Skaha, client, service

**Science Platform Server**:
Deployable CANFAR-compatible server endpoint that accepts authenticated platform requests.
_Avoid_: Base URL, host, cluster

**Server Name**:
Required, unique, user-facing handle for one **Science Platform Server**, used to reference it in configuration and commands.
_Avoid_: Label, alias, key

**VOSpace Service**:
Storage service associated with a **Science Platform Server**, identified by an IVOA registry resource URI and accessed through a base HTTP endpoint.
_Avoid_: Storage backend, filesystem

**Storage Name**:
Required, globally unique, user-facing handle for one **VOSpace Service**. `local` is reserved for the user's local filesystem.
_Avoid_: Server Name, alias, key

**Identity Provider (IDP)**:
Organization that issues user identity for CANFAR authentication.
Initial IDPs are `Canadian Astronomy Data Centre (CADC)` and `SKA Regional Centre Network (SRCNet)`.
_Avoid_: Provider

**Authentication**:
Domain seam that owns identity lifecycle, authentication state, and authentication method.
_Avoid_: Auth service, login system

**Platform**:
Domain seam that owns Science Platform Server discovery, selection, and platform metadata.
_Avoid_: Target service, environment service

**Authentication Record**:
Saved Authentication state for one Identity Provider, including credential mode and expiry.
_Avoid_: Context, account, login

**Authentication Mode**:
Credential mechanism used by an Authentication Record.
_Avoid_: Provider

**Server Selection**:
User's chosen **Science Platform Server** for new platform requests.
_Avoid_: Platform Context, target

**Server Discovery Scope**:
Boundary that determines which **Science Platform Servers** are considered during discovery, such as production-only or development-inclusive.
_Avoid_: Discovery flag, server environment

**Session**:
User-owned compute environment launched on a Science Platform Server.
_Avoid_: Job, pod, container

**Session Kind**:
Category of Session experience requested by a user.
_Avoid_: Type, app

**Container Image**:
Reusable software environment used to start a Session.
_Avoid_: Container, package

**Container Registry**:
Image catalog where CANFAR Container Images are published and discovered.
_Avoid_: Harbor, image server

**Resource Allocation Mode**:
Policy for how CPU, memory, and GPU resources are requested for a Session.
_Avoid_: Resource profile, quota

## Relationships

- A **CANFAR Science Platform** exposes one or more **Science Platform Servers**.
- A **Science Platform Server** is identified by its **Server Name**; its IVOA URI is discovery metadata, and two Server Names may point at the same endpoint.
- A **Science Platform Server** can expose multiple **VOSpace Services**.
- A **VOSpace Service** is identified by its **Storage Name** and uses its parent **Science Platform Server**'s **Identity Provider (IDP)**.
- An **Identity Provider (IDP)** can support one or more **Science Platform Servers**.
- **Authentication** and **Platform** are separate seams with independent ownership.
- An **Authentication Record** belongs to one **Identity Provider (IDP)**.
- An **Authentication Record** uses one **Authentication Mode**.
- A **Server Selection** refers to one **Science Platform Server** by its **Server Name**.
- A **Server Discovery Scope** constrains candidate **Science Platform Servers** before **Server Selection**.
- A **Server Selection** and **Authentication Record** together determine where new platform requests go.
- A **Session** runs on one **Science Platform Server**.
- A **Session** has one **Session Kind**.
- A **Session** starts from one **Container Image**.
- A **Container Registry** publishes many **Container Images**.
- A **Resource Allocation Mode** shapes resources requested for a **Session**.

## Example dialogue

> **Dev:** "When a user switches Authentication, does an existing Session move?"
> **Domain expert:** "No. Authentication changes active identity for new requests; existing Sessions remain on the Science Platform Server where they were launched."

## Flagged ambiguities

- "context" can mean Python execution context or legacy config context. In CANFAR domain docs, use explicit term names and avoid bare "context".
