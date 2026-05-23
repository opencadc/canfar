# CANFAR

CANFAR is a science platform context for authenticated astronomical compute, container images, and user sessions. This glossary names domain concepts only; implementation details live in code and ADRs.

## Language

**CANFAR Science Platform**:
Cloud-native environment for astronomical research workflows.
_Avoid_: Skaha, client, service

**Science Platform Server**:
Deployable CANFAR-compatible server endpoint that accepts authenticated platform requests.
_Avoid_: Base URL, host, cluster

**Identity Provider (IDP)**:
Organization that issues user identity for CANFAR authentication.
Initial IDPs are `Canadian Astronomy Data Centre (CADC)` and `SKA Regional Network (SRCNet)`.
_Avoid_: Provider

**Authentication**:
Domain seam that owns identity lifecycle, authentication state, and authentication method.
_Avoid_: Auth service, login system

**Platform**:
Domain seam that owns Science Platform Server discovery, selection, and platform metadata.
_Avoid_: Target service, environment service

**Authentication Context**:
Saved profile for Authentication state, including selected IDP and authentication method.
_Avoid_: Account, config, login

**Authentication Mode**:
Credential mechanism used by an Authentication Context.
_Avoid_: Provider

**Server Selection**:
User's chosen **Science Platform Server** for new platform requests.
_Avoid_: Platform Context, target

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
- An **Identity Provider (IDP)** can support one or more **Science Platform Servers**.
- **Authentication** and **Platform** are separate seams with independent ownership.
- An **Authentication Context** belongs to one **Identity Provider (IDP)**.
- An **Authentication Context** uses one **Authentication Mode**.
- A **Server Selection** belongs to one **Science Platform Server**.
- A **Server Selection** and **Authentication Context** together determine where new platform requests go.
- A **Session** runs on one **Science Platform Server**.
- A **Session** has one **Session Kind**.
- A **Session** starts from one **Container Image**.
- A **Container Registry** publishes many **Container Images**.
- A **Resource Allocation Mode** shapes resources requested for a **Session**.

## Example dialogue

> **Dev:** "When user switches Authentication Context, does existing Session move?"
> **Domain expert:** "No. Authentication Context changes active identity for new requests; existing Session remains on the Science Platform Server where it was launched."

## Flagged ambiguities

- "context" can mean Python execution context, config context, or **Authentication Context**. In CANFAR domain docs, use explicit term names and avoid bare "context".
