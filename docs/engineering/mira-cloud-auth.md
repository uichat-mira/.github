# Mira Cloud Authentication Design v0

Status: Design  
Owner: Mira Cloud  
Last reviewed: 2026-10-25 (Phase III product revision)  
Research owner: [mira-desktop#418](https://github.com/uichat-mira/mira-desktop/issues/418)  
Roadmap context: [mira-desktop#315](https://github.com/uichat-mira/mira-desktop/issues/315)  
Organization baseline: [Mira Cloud Core Specification](./mira-cloud.md)

> This document records the design conclusion of AGT-025. It is a design contract, not a claim that Cloud Authentication is already implemented or deployed.

## 0. Phase III maintainer decision · 2026-10-25 (supersedes conflicting AGT-025 V0 assumptions)

**Product scope is frozen in [Phase III roadmap #315](https://github.com/uichat-mira/mira-desktop/issues/315).** This section updates the 2026-10-22 research conclusions; it is a design and implementation target, not a claim that OAuth/Host grants already run in production. Existing Cloud Auth account/password, Cloud Session, Mira Device and audience-bound Shiyan/Relay credentials are retained rather than rewritten.

### Two distinct user-facing remote entry paths

1. **Cloud entry**: Desktop and Mobile sign into the *same* Mira Cloud Account, register as separate installations and automatically associate/discover a usable Desktop Host. They do **not** repeat QR pairing, one-time pairing claims or on-site Desktop approval. At Desktop Cloud login, the owner explicitly defines the Mobile Host capability/scope grants. OAuth 2.0 is the chosen authorization protocol for this entry, with OIDC if needed for standard client identity semantics; root username/password still uses existing Mira Cloud Account authority. Later grant edits and revocations are managed from the Cloud Auth account/device authorization UI without physical Desktop access. Day-to-day Tool calls do not initiate a fresh interactive OAuth authorization or synchronous Cloud introspection per invocation.
2. **Non-Cloud entry**: Tailscale Direct continues with the existing Remote V1 QR/Host-approved pairing and Host-owned device credential. It requires no Cloud Account. Cloud hosted Relay and no-cloud Tailscale are **independent entry paths**: no automatic Direct↔Relay fallback, shared entry identity, accidental cross-path credential reuse or opaque automatic switching.
3. Mobile remains local-first; its own local camera/files etc remain available to Mobile itself. Phase III **does not** let Desktop or another Agent remotely invoke Mobile camera, location, files or device capabilities.

### Authentication, grant and execution authorities

- **Cloud Auth**: existing account/password and revocable device-bound sessions; standard OAuth 2.0 authorization for the new cross-device Cloud Host entry; explicit Desktop→Mobile, scoped Host grant record and revocation authority; Cloud Portal grant management. Device registration alone is *not* blanket Tool permission. The Desktop defines permitted scopes at login; registered same-account devices can associate without an extra in-person step.
- **Hosted Relay**: separately audience-bound connection ticket, room and role; transport frames only. A `relay:transport` ticket cannot authorize a Desktop business route.
- **Desktop Remote Gateway / Harness**: validates an effective, cached or verifiable Host grant and applies existing Host owner/capability scope, canonical route, Policy and exact-invocation approval. Only individual Tool-level high-risk operations may need their existing in-session confirmation; this is distinct from the eliminated **device pairing approval**. No network call to Cloud Auth for every Tool operation.
- **Grant lifecycle**: engineering must settle OAuth 2.0/OIDC endpoint/client registration and native-app PKCE exchange where applicable, audience/Host+Mobile binding, scope, lifetime, revocation/version propagation and fail-closed semantics. Cloud grant changes must become effective at Host according to an explicitly testable bounded contract, rather than only vanishing from a UI device list; do not claim instant remote revocation when Host is disconnected and operating on previously valid offline evidence. This is an engineering protocol decision, not an unresolved product decision.
- Preserve Remote V1 manifest, scope mapping, Gateway, Tool Gateway, Host-owned AgentRun and Artifact authority; do not create a second capability registry or general-purpose permission engine. How a Cloud grant is bridged into Remote V1 authority is the narrow G research/implementation outcome in #315, **not** implicitly an expansion of closed OPS-006 or existing two-audience OPS-008.

### Shiyan, future Cloud MCP and migration

- Signed-in Cloud users access **new Cloud Shiyan** without a second end-user login. New Shiyan business data is isolated by Mira Cloud Account at the Shiyan service authorization boundary. **No compatibility migration of legacy Shiyan user data**; legacy credential/code may be retired based on real consumers but is not a pilot acceptance requirement.
- Future Cloud MCP services may reuse the Cloud Account, audience-bound service credentials and service-specific account isolation pattern established by new Shiyan. Building a general Cloud MCP ecosystem is **not** a required Phase III delivery.
- Only two actual users presently exist. Do not create a legacy end-user migration program for obsolete mixed Remote pairing state; preserve the still-supported no-cloud Tailscale product path itself.
- Existing implementation remains observable truth: account/password + Cloud Sessions (OPS-006), Mira Device lifecycle on `cloud-auth/dev` (OPS-007), Shiyan/Relay JWT + JWKS on `dev` (OPS-008), Remote V1 Host `mira_device_*` and mixed selection. Documentation of the *target* does not mean new OAuth endpoints, Host grants, Portal controls, or standalone Cloud Relay entry have been implemented.

### Required Phase III verification

Real Desktop and Mobile sign into one Cloud account → automatic association/discovery of eligible Desktop Host → login-time grant permits scoped Mobile invocation over hosted Relay without QR/on-site approval → changes/removals through Cloud Auth Portal are enforced at Host → a high-risk operation receives its *specific* Harness approval if required → logout/revocation and Cloud/Relay/Host downtime are handled correctly. Separately prove independent no-cloud Tailscale pairing; new Shiyan cross-account data isolation; no cross-entry implicit fallback or unintended Mobile device exposure.

---

## 1. Product conclusion

Mira Cloud Account is the unified user identity for Mira-operated cloud services.

A user authenticates once to Mira Cloud and may then use the Mira Cloud services for which the account is allowed, including Cloud Shiyan, the hosted Mira Relay, cloud device discovery, and future Mira Cloud services. Individual services do not create independent end-user account systems.

Mira remains local-first:

- Desktop and Mobile local functions do not require Mira Cloud Account.
- Local/Direct cross-device use does not require Mira Cloud Account.
- Tailscale + Remote Host V1 remains a supported no-cloud-account route.
- Mira-operated cloud services and cloud-mediated routes require Mira Cloud Authentication.
- Hosted Mira Relay is a Mira Cloud service; Relay transport does not become the owner of Host business authorization.

The product interaction is intentionally not over-specified here. The user-facing experience may expose Cloud sign-in and Local/Direct connection in different UI forms. The identity contract must not depend on a particular first-run screen or QR flow.

## 2. V0 account admission and root authentication

Mira Cloud V0 is closed-access.

### Confirmed V0 policy

- No public self-registration.
- No invitation-code system.
- No application/review workflow.
- Accounts are provisioned or allowed by maintainers.
- Root authentication uses account name + password.
- An account must also be allowed to use Mira Cloud services.
- Self-service password recovery is not required for V0; an administrator reset path is sufficient for the closed pilot.

The allowlist is an admission control, not a second identity system. The account remains the identity; allow/disable state determines whether the account may obtain usable Mira Cloud sessions and service grants.

Password storage must use Argon2id or a later explicitly reviewed replacement, never plaintext or reversible encryption. V0 should start from current OWASP-grade Argon2id parameters and benchmark them on the actual 2 vCPU / 2 GiB self-managed server so password verification remains intentionally expensive without creating an avoidable denial-of-service surface. Exact cost parameters remain implementation/security tuning rather than product constants.

## 3. Identity model

The following principals are distinct:

### Mira Cloud Account

Represents the human/user identity used across Mira Cloud services.

It does not replace a Desktop local user, Remote Host owner, Provider credential, or third-party account.

### Mira Device

Represents one Mira Desktop or Mira Mobile installation registered under a Mira Cloud Account.

V0 should treat a device as an installation identity, not a hardware serial number, IMEI, MAC address, or other physical hardware identifier. Reinstall may create a new Mira Device unless a later recovery design explicitly preserves identity.

### Desktop Host

A Mira Desktop installation may act as a Remote Host. Host business state and Host authorization remain authoritative on the Desktop.

Cloud device registration by itself does not grant blanket Host Tool authority. For the Cloud entry, same-account Desktop/Mobile installations auto-associate under scopes deliberately granted when Desktop signs in; Remote Host enforces the effective grant. No QR/in-person claim is required.

### Cloud Session

Represents a signed-in device session for a Mira Cloud Account. It is revocable and belongs to a specific Mira Device.

### Service credential / grant

A service-specific, short-lived credential derived from a valid Cloud Session. It is restricted to an intended audience such as Shiyan or Relay.

A single universal bearer credential must not be stretched across all Mira Cloud services.

## 4. Current technical reality

| Principal / path | Current credential or state | Current authority | Research conclusion |
| --- | --- | --- | --- |
| Desktop local user | Desktop-local password/JWT/user row | Desktop local backend | Remains local; not Mira Cloud Account |
| Remote V1 paired device | Opaque `mira_device_<deviceId>.<secret>`, Host stores token hash and scopes | Desktop Host | Preserved for Local/Direct Remote V1 |
| Mobile Remote Host connection | Device credential stored in native secure storage with Host URL/device/scopes | Paired Desktop Host | Preserved; not promoted into Cloud identity |
| Hosted Relay V1 | Relay room Host/Client transport tokens; hashes stored by Relay room | Relay transport only | Must converge to Cloud-issued connection eligibility for hosted Relay without taking Host business authority |
| Cloud Shiyan | Existing Shiyan device credential compatibility path | Shiyan service | Compatibility only; converge to shared Cloud identity |
| Mira Cloud Account / shared Device identity | Not implemented | None | New V0 implementation required |

Evidence:

- [Desktop Remote Host V1 protocol](https://github.com/uichat-mira/mira-desktop/blob/dev/docs/remote-access/mobile-host-protocol-v1.md)
- [Desktop Remote pairing implementation](https://github.com/uichat-mira/mira-desktop/blob/dev/server/src/services/remote-access-pairing.service.ts)
- [Desktop Remote device auth](https://github.com/uichat-mira/mira-desktop/blob/dev/server/src/services/remote-device-auth.service.ts)
- [Mobile device credential store](https://github.com/uichat-mira/mira-mobile/blob/dev/src/security/deviceCredentialStore.ts)
- [Mobile Remote Host client](https://github.com/uichat-mira/mira-mobile/blob/dev/src/api/remoteMiraHost.ts)
- [Cloud Shiyan](https://github.com/uichat-mira/cloud-shiyan)
- [Mira Relay](https://github.com/uichat-mira/uichat-mira-relay)

## 5. Trust and authorization boundaries

Authentication and authorization are separate.

### Mira Cloud Auth owns

- Mira Cloud Account identity.
- password verification;
- account allow/disable state;
- Mira Device registration/revocation;
- Cloud Session issuance/revocation;
- service credential issuance;
- Phase III OAuth 2.0-based Cloud Host grant issuance/management/revocation as a separately scoped implementation outcome (not part of the completed OPS-006 or existing OPS-008 two-audience service contract).

### Cloud Shiyan owns

- Shiyan-specific authorization and business policy;
- CaptureTask and Destination behavior;
- Shiyan service data.

Cloud Shiyan accepts shared Mira Cloud identity but does not become the Cloud Account authority.

### Hosted Mira Relay owns

- connection eligibility;
- room addressing;
- transport connection establishment;
- forwarding.

Hosted Relay remains transport-only. It must not interpret Browser, Terminal, Agent, Thread, Remote Host scopes, or Desktop business data.

### Desktop Host owns

- Remote V1 pairing and device scopes for Local/Direct access;
- capability visibility/execution;
- Harness Policy;
- exact invocation validation;
- Host-side business ownership;
- final execution.

A human approval may be presented on the terminal currently used by the user, including Mobile. Desktop's responsibility is to verify that the approval is bound to the exact pending invocation and then execute according to Host policy; the product must not require the person to physically return to the Desktop merely to approve a Mobile-originated operation.

## 6. V0 credential architecture

The recommended minimal model is:

```text
account + password
      |
      v
Mira Cloud Session
      |
      +----> Shiyan service access credential
      |
      +----> hosted Relay connection ticket
      |
      +----> future service-specific credentials
```

### Cloud Session

Recommended V0 shape: a high-entropy opaque session/refresh credential stored in OS secure storage. The server stores only a hash or otherwise supports direct revocation.

The user should normally sign in once and remain signed in. Session lifetime is an engineering policy, not a user-visible product timer.

### Service access credential

Recommended V0 shape: short-lived, asymmetrically signed, audience-bound token. JWT is the preferred concrete starting format because the Organization contract already requires issuer, subject, audience, scope/capability and expiry semantics; the exact signing algorithm is an implementation/runtime choice.

A Shiyan credential should be valid for Shiyan, not Relay.

### Relay connection ticket

Hosted Relay should use a short-lived connection ticket obtained through Mira Cloud identity.

A ticket is scoped to the Relay service and the connection context (for example Relay room and role). Ticket expiry prevents a new connection from being established with an old ticket; it does not by itself terminate an already-established WebSocket.

The hosted Relay must continue to keep Remote Host business authorization outside the Relay protocol.

## 7. Device registration alternatives

Two minimal approaches were considered.

### Alternative A — installation ID + secure Cloud Session

Each installation generates a random local installation identity, registers it as a Mira Device after account authentication, and stores the Cloud Session in OS secure storage.

Advantages:

- smallest V0 implementation;
- straightforward logout/device revocation;
- fits the closed allowlist pilot;
- no hardware identifiers.

Risks:

- stolen bearer session material can be replayed until revoked/expired;
- device identity is mainly a server record plus possession of session material.

### Alternative B — per-device asymmetric key pair / proof of possession

Each installation generates a key pair, retains the private key in secure storage, and registers the public key with Mira Cloud. Service credentials can be bound to the device key.

Advantages:

- stronger stolen-token resistance;
- stronger long-term device identity;
- better foundation for higher-risk delegated operations.

Costs:

- key lifecycle, recovery/reinstall and proof-of-possession protocol complexity;
- more implementation and migration work before it improves the closed pilot experience.

### V0 decision

Use Alternative A for the first implementation slice. Keep the schema and contracts capable of later attaching a device public key. Do not make hardware identity a dependency.

Per-device proof of possession is a hardening step, not a blocker for the first unified-login pilot.

## 8. Service authentication alternatives

Two service access models were considered.

### Alternative 1 — online introspection for every service request

Every Shiyan/Relay authorization request calls Cloud Auth to validate an opaque credential.

Benefits: immediate central revocation and simple service-side token logic.

Costs: Cloud Auth becomes a latency and availability dependency for every service request; a Cloud Auth outage can break already-authenticated service use and produces worse user experience.

### Alternative 2 — revocable Cloud Session + short-lived signed service credentials

Cloud Auth owns the revocable account/device session. Services locally verify short-lived, audience-bound credentials.

Benefits:

- unified sign-in without making Auth a per-request bottleneck;
- service credentials remain narrow;
- temporary Auth unavailability does not automatically invalidate an already-established Relay connection;
- service runtimes can verify identity independently.

Tradeoff: central revocation of already-issued short-lived service credentials is bounded by their remaining lifetime unless a service adds an online revocation check.

### V0 decision

Use Alternative 2.

Exact numeric TTLs are deliberately not frozen by this product research. Implementation must choose safe defaults and test refresh/revocation behavior without exposing token timers to users.

## 9. User-experience failure semantics

The product must distinguish failures instead of collapsing them into one "offline" state.

| Condition | User-visible meaning | Required behavior |
| --- | --- | --- |
| Mira Cloud temporarily unreachable | Cloud unavailable, not "logged out" | Keep local features and Local/Tailscale working; do not erase session state merely because Auth cannot be reached |
| Account/session revoked or truly expired | Re-authentication required | Ask user to sign in again; preserve local functions |
| Shiyan unavailable | Shiyan service problem | Do not describe it as an account failure unless identity is actually rejected |
| Desktop Host offline | That Desktop is offline | Show device/Host state |
| Relay transport disconnected | Remote transport interrupted | Reconnect automatically when practical; only surface failure when recovery cannot complete |
| Hosted Relay needs a new ticket while Cloud is unavailable | Cloud route cannot currently be re-established | Do not break Local/Tailscale; explain that the cloud remote route is temporarily unavailable |

Experience rule:

> Do not make users maintain authentication state. Already-established work should continue when safely possible; creating a new Mira-operated cloud relationship requires valid Cloud authorization.

## 10. Lifecycle policy

The research intentionally does not freeze "15 minutes", "30 days", or another numeric lifetime as product truth.

Implementation must satisfy these semantics:

- routine refresh is silent;
- a brief Cloud outage must not immediately make the UI claim the user signed out;
- local capabilities never depend on Cloud session freshness;
- an already-established Relay WebSocket is not closed solely because the connection ticket later expires;
- new hosted Relay connections require currently acceptable cloud authorization;
- a locally revoked Host grant takes effect according to Host state even if Cloud is unavailable;
- a Cloud-account or device revocation must prevent future Cloud credential refresh/issuance.

Numeric TTLs belong to implementation/security tuning and may evolve without changing the product contract.

## 11. V0 persistence model

The minimum Cloud Auth persistent model is conceptually:

```text
accounts
devices
sessions
allowlist/admission
```

The exact schema is implementation-owned. It must support:

- unique account identity;
- password hash;
- account allowed/disabled state;
- device ownership and revocation;
- session hashing/revocation/expiry;
- audit timestamps needed for security and support.

No Provider API keys, Desktop secrets, user files, Remote Host business data, prompts, or Relay payload bodies belong in Cloud Auth.

## 12. Runtime / deployment recommendation

Create a dedicated Mira Cloud Auth service boundary, conventionally `cloud-auth`, rather than embedding shared identity into Shiyan, Relay, or the current `mira-cloud-infra` New API deployment.

### V0 deployment decision

The default V0 deployment is the Mira self-managed cloud server rather than Cloudflare Worker + D1.

Recommended V0 stack:

- Node.js LTS + TypeScript;
- Fastify as the HTTP service framework;
- SQLite in WAL mode as the initial persistent store;
- a thin repository/storage boundary so the service contract is not coupled to SQLite-specific behavior throughout the codebase;
- one Docker image/container for the application;
- a persistent host volume for the SQLite database;
- the existing server Caddy layer for TLS and reverse proxy;
- structured JSON logs with rotation;
- a consistent SQLite backup path to external/object storage;
- no Redis or PostgreSQL solely for V0 Cloud Auth.

The reasoning is operational rather than ideological: Mira now has a long-lived self-managed server, Cloud Auth is a small stateful identity root, the expected V0 write rate is low, and keeping account/device/session state on one controlled node gives a simpler failure and backup model than introducing a second distributed control plane only for authentication.

### Resource budget

The initial server is 2 vCPU / 2 GiB RAM / 40 GiB disk. Cloud Auth should remain deliberately small:

- ordinary application memory target: roughly 100–200 MiB;
- container hard memory ceiling: approximately 512 MiB unless evidence justifies a change;
- CPU is expected to be low outside password hashing; password-hash concurrency and login rate limits must prevent Argon2id from exhausting the host;
- persistent Cloud Auth data, WAL, local backup staging and bounded logs should fit comfortably within a few GiB;
- Docker/application log rotation is required so logs cannot grow without bound.

These are operational budgets, not protocol guarantees. Implementation may tune them from measured evidence without changing Mira Cloud Account semantics.

### Migration boundary

SQLite is selected because V0 is a single-instance service with small transactional state. A move to PostgreSQL should be triggered by an architectural need such as multiple active service instances, HA/failover, or another proven persistence requirement—not by an arbitrary account-count threshold.

The service must keep HTTP, identity, and credential contracts independent from the persistence engine. Clients and service consumers must not know whether Cloud Auth uses SQLite, PostgreSQL, Worker/D1, or another backend.

This remains a deployment choice, not a permanent topology contract. A later migration to PostgreSQL, another host, a multi-node topology, or even another compatible runtime must not require redefining Mira Cloud Account semantics.

The server location, ICP/domain status, and concrete public hostname remain deployment concerns rather than identity prerequisites.

## 13. Migration / implementation order

Implementation should proceed in independently verifiable slices:

1. **Cloud Auth core** — account/password, admission allowlist, device registration, session issue/revoke, minimal account/device APIs.
2. **Service credential contract** — audience-bound signed access credentials and verifier contract.
3. **Cloud Shiyan consumer** — accept Mira Cloud identity while preserving the existing Shiyan device credential only as a bounded migration compatibility path.
4. **Hosted Relay consumer** — replace hosted-service user-facing static Relay credentials with Cloud-issued connection tickets while keeping Relay transport-only.
5. **Desktop/Mobile product integration** — sign-in/session storage/device registration, service consumption, device revoke/logout UX.
6. **Hardening after pilot evidence** — optional device public-key proof of possession, self-service recovery, broader admission/registration, richer device management.

Do not create a second Remote Capability Registry, a second Host business authorization model, or a second pairing protocol.

## 14. Required / unnecessary / deferred

### Required for the first unified-cloud-auth pilot

- dedicated Cloud Auth boundary;
- closed allowlist;
- account/password authentication;
- Mira Device registration;
- revocable Cloud Session;
- service-specific access credentials;
- Shiyan shared-identity integration;
- hosted Relay connection eligibility derived from Cloud identity;
- Local/Tailscale route preserved independently;
- under the 2026-10-25 Phase III amendment: OAuth 2.0 Cloud Host authorization, same-account automatic Desktop/Mobile association, login-time scope grant, and Cloud Portal grant changes/revocation without on-site pairing (the grant bridge is the separately owned G outcome in #315).

### Not required

- public registration;
- invite codes;
- application/review workflow;
- email verification;
- third-party/social-provider login (distinct from the standard OAuth 2.0 authorization required for the Phase III Cloud Host entry);
- Passkeys;
- user-facing token management;
- Redis/PostgreSQL solely for V0 Auth;
- Cloud ownership of Remote Host business authorization.

### Deferred

- exact final UI layout and QR interaction;
- self-service password reset;
- per-device asymmetric proof of possession;
- public/community registration;
- organization/team accounts;
- multi-region identity topology;
- precise token/session TTL tuning beyond safe V0 defaults;
- multi-instance/HA database topology before evidence requires it.

## 15. Effect on Phase III

This original AGT-025 research did not add a third Phase III product goal; **the maintainer has since revised #315 on 2026-10-25, and §0 of this document is its authorized design delta**.

For Desktop ↔ Mobile cross-device capability:

- Local/Direct/Tailscale journeys can continue without Mira Cloud Account.
- journeys that consume hosted Mira Relay, cloud discovery, or another Mira-operated cloud intermediary require Mira Cloud Authentication.
- Remote V1 paired-device scopes, canonical Host routes, Mobile Gateway/Registry and Host business authorization remain the cross-device capability contract.

Any roadmap wording change must be separately authorized and made in #315; this document does not silently mutate that roadmap.

## 16. Research acceptance samples

The design is considered sufficient for implementation decomposition when the following scenarios have an unambiguous owner and outcome:

1. A non-cloud user can use Desktop/Mobile locally and pair through Local/Tailscale without Mira Cloud.
2. An allowed account can sign in once and consume Shiyan without a second Shiyan account.
3. The same account can obtain hosted Relay connection eligibility without manually maintaining a separate Relay user token.
4. Relay transport cannot authorize Browser/Terminal/Agent operations by itself.
5. A Mobile-originated high-risk Host invocation can be approved from Mobile while Desktop verifies the exact invocation and remains execution authority.
6. A brief Cloud outage does not claim the user is logged out and does not break local features.
7. A revoked Cloud device cannot refresh/obtain new cloud service credentials.
8. A Host that is offline is presented as Host offline, not account failure.
9. Reinstall/new installation creates a distinct Mira Device unless a later recovery feature explicitly rebinds it.
10. Existing Shiyan/Relay compatibility credentials are migration mechanisms, not the new organization-wide identity.

