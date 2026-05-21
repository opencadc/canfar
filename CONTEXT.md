# CANFAR

CANFAR is a science platform context for authenticated astronomical compute, container images, and user sessions. This glossary names domain concepts only; implementation details live in code and ADRs.

## Language

**CANFAR Science Platform**:
Cloud-native environment for astronomical research workflows.
_Avoid_: Skaha, client, service

**Science Platform Server**:
Deployable CANFAR-compatible server endpoint that accepts authenticated platform requests.
_Avoid_: Base URL, host, cluster

**Authentication Context**:
Saved profile that selects one Science Platform Server and its credentials.
_Avoid_: Account, config, login

**Authentication Mode**:
Credential mechanism used by an Authentication Context.
_Avoid_: Provider, method

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
- An **Authentication Context** belongs to exactly one **Science Platform Server**.
- An **Authentication Context** uses one **Authentication Mode**.
- A **Session** runs on one **Science Platform Server**.
- A **Session** has one **Session Kind**.
- A **Session** starts from one **Container Image**.
- A **Container Registry** publishes many **Container Images**.
- A **Resource Allocation Mode** shapes resources requested for a **Session**.

## Example dialogue

> **Dev:** "When user switches Authentication Context, does existing Session move?"
> **Domain expert:** "No. Authentication Context changes where new requests go; existing Session remains on Science Platform Server where it was launched."

## Flagged ambiguities

- "context" can mean Python execution context, config context, or **Authentication Context**. In CANFAR domain docs, use **Authentication Context** for saved server-plus-credential profiles.
