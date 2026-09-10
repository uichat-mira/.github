# Mira Cloud Core Specification

Mira Cloud is the organization-wide name for Mira's network-facing backend services.

It defines a shared service model, naming convention, client boundary, and authentication semantics. It does **not** require every backend capability to live in one repository, one Worker, or one deployment unit.

## 1. Scope

Mira Cloud includes backend services that are reachable by Mira clients or other Mira services, including services such as Relay, Shiyan, Search, Provider gateways, and shared identity/authentication infrastructure.

Cloudflare Workers is the preferred runtime for current Mira Cloud services where it fits, but `Mira Cloud` is a product and architecture boundary, not a synonym for Cloudflare Workers. A service may later use D1, R2, Queues, Workflows, Durable Objects, or non-Cloudflare infrastructure without leaving Mira Cloud.

## 2. Naming

New dedicated Mira Cloud runtime repositories SHOULD use:

```text
cloud-<service>
```

Examples:

```text
cloud-shiyan
cloud-auth
cloud-search
```

Existing repositories do not need to be renamed only for cosmetic consistency. Repository migration and service renaming are separate changes unless there is a concrete operational reason to combine them.

Runtime service names SHOULD use a stable `mira-<service>` form where the platform requires a deployment name.

## 3. One service does not mean one monolith

A Mira Cloud service SHOULD default to the smallest practical number of deployment units.

Separate Workers or services are justified when they provide a real boundary such as:

- independent security or secret scope;
- independent scaling or resource limits;
- independent release cadence;
- fault isolation;
- reuse by multiple products or services.

Code modularity alone is not sufficient reason to create another deployment unit. Internal modules MAY remain strongly separated even when deployed together.

## 4. Stable client boundary

Mira clients MUST depend on stable Mira Cloud contracts, not deployment topology.

Clients SHOULD NOT treat `workers.dev` URLs, Worker names, repository names, or Service Binding names as public API contracts.

The target public namespace is:

```text
api.mira.tomz.io/<service>/...
```

When a service has not yet moved behind that namespace, its current endpoint is a compatibility detail and SHOULD be replaceable without changing product-level contracts.

## 5. Unified identity, service-specific authorization

Mira Cloud SHALL converge on a shared identity layer.

The shared identity model MUST be able to represent at least:

- User identity;
- Mobile or other client Device identity;
- Desktop Host identity;
- Service identity.

Unified authentication answers **who or what is making the request**. Individual services remain responsible for deciding **what that identity may do in the current context**.

A single global credential MUST NOT be stretched to represent every temporary capability or business permission.

Service-specific short-lived credentials remain valid where appropriate, including upload grants, pairing/session credentials, delegated capabilities, and similar scoped tokens.

Provider API keys and third-party credentials are not Mira user identity. They MUST remain within the service or client boundary that owns them and MUST NOT become general Mira Cloud authentication credentials.

## 6. Authentication contract before token format

The organization standardizes authentication semantics before standardizing a concrete token technology.

Any future shared Mira Cloud credential format MUST carry enough information to establish, directly or indirectly:

- issuer;
- subject identity;
- intended audience/service;
- granted scope or capability;
- expiry/lifetime;
- revocation or invalidation strategy where required.

This specification does not currently mandate JWT, opaque tokens, OAuth, or a specific identity provider. Those are implementation decisions for the Mira Cloud Auth design.

## 7. Secrets and trust boundaries

Secrets belong to the narrowest runtime boundary that requires them.

Organization-level deployment credentials MAY be shared when they represent common infrastructure access, but application/provider secrets SHOULD remain service-specific unless a shared service explicitly owns them.

A public HTTP entrypoint does not grant callers access to runtime secrets. Nevertheless, splitting a service remains appropriate when secret isolation itself is a required security boundary.

## 8. Source of truth

Organization-wide Mira Cloud rules live in `uichat-mira/.github`.

Repository-specific implementation details live in the repository that owns the service.

Actual deployed configuration and runtime state remain the technical truth for what is currently running. Documentation MUST NOT claim a migration, endpoint, binding, or authentication path is active until it has been verified in the real environment.

## 9. Migration rule

Do not use Organization migration as a pretext for unrelated architecture rewrites.

When a service migration and an architecture change are both desired, preserve a rollback anchor and make each change independently verifiable. A clean new repository MAY be used when the architecture boundary itself is intentionally being replaced, but the old repository/deployment MUST remain available until the new path passes real acceptance.

## 10. Current direction

For new Mira Cloud work, prefer:

```text
one clear service boundary
+ one stable public contract
+ one shared identity model
+ the fewest practical deployment units
```

Split later when a real operational boundary appears; do not pre-build distributed complexity only because the platform makes it easy.
