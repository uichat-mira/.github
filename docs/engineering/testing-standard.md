# Mira Organization Testing Standard

Status: Core engineering policy

This document defines the shared testing language and promotion gates for repositories in the `uichat-mira` Organization.

The Organization standardizes **test responsibilities, command semantics, CI evidence, and promotion gates**. It does **not** require every repository to use the same test runner.

Repository-native runners remain valid where they fit the platform best. Examples include Vitest for Mira Desktop, Jest for Mira Mobile, and the Cloudflare Workers Vitest integration for Mira Cloud services.

## 1. Core rule

A repository must make it possible to answer five different questions separately:

1. Does an isolated unit behave correctly?
2. Do boundaries and protocols still satisfy their contracts?
3. Do components work together in the target runtime?
4. Does the critical user/service journey work across a deployed environment?
5. Is the deployed production version actually healthy?

Passing a lower layer is not evidence that a higher layer passed.

## 2. Shared test layers

### T1 — Unit

Purpose: fast local correctness of pure logic and narrowly scoped modules.

Properties:

- deterministic;
- no production network dependency;
- no real external credentials;
- safe to run on every relevant PR/push;
- failures identify a small code surface.

Examples: parser behavior, state reducers, policy decisions, path generation, retry classification, provider normalization.

### T2 — Contract

Purpose: prove stable boundaries independently of a full deployment.

Typical contracts:

- HTTP request/response shapes;
- Remote Host / Mobile protocols;
- Agent / Tool / MCP contracts;
- provider adapter contracts;
- Destination idempotency and failure semantics;
- persistence schema and migration invariants;
- auth token/credential semantics.

Contract tests should prefer fixtures, fakes, or protocol-level mocks over fragile UI or infrastructure setup.

A contract owned by one repository and consumed by another must have an explicit canonical owner. Consumer tests may mirror the contract, but must not silently redefine it.

### T3 — Runtime integration

Purpose: execute meaningful behavior in the runtime that owns it.

Examples:

- Cloudflare Worker tests in `workerd` with D1/R2/Workflow bindings;
- Desktop server tests in Node and UI integration tests in jsdom/browser runtime;
- Mobile component/service tests in the React Native/Jest runtime;
- integration of repository, service, adapter and persistence layers.

Mock only external boundaries that are not the subject of the test. Do not mock away the runtime capability being verified.

### T4 — Environment E2E

Purpose: prove a critical journey against a deployed non-production environment or version preview.

Examples:

- Mobile → Cloud API → Workflow → Destination;
- Desktop ↔ Relay ↔ Mobile pairing and request path;
- authenticated Mira Cloud service calls;
- package/site preview deployment and smoke.

T4 evidence belongs to the deployed version/environment, not merely to the source commit that produced it.

A repository need not run a large E2E suite for every feature PR. Critical journeys should run when promoting toward `test`/`prod`, or when a change directly touches that journey.

### T5 — Production smoke

Purpose: prove that the exact production deployment is alive and its minimum critical path works after release.

Production smoke must be:

- small;
- non-destructive or explicitly disposable;
- fast enough to support rollback decisions;
- tied to an exact deployment/version/release identifier.

A successful deploy command is not a successful T5 smoke.

## 3. Organization command contract

Where a repository has a package/task runner, expose these logical commands where applicable:

```text
test:unit
test:contract
test:integration
test:e2e
smoke
check
```

Repositories may omit a layer that genuinely does not apply, but should document the omission locally.

`check` is the fast merge gate. It should normally include static/type checks plus T1/T2 and selected T3 tests that are cheap and deterministic. It must not quietly trigger production deployment or destructive external tests.

The underlying implementation is repository-specific. Examples:

```text
Desktop   -> Vitest / Testing Library / platform build checks
Mobile    -> Jest / React Native preset / native build checks
Cloud     -> Vitest + @cloudflare/vitest-plugin / Wrangler
Docs      -> Node/Vitest-compatible package tests / build / preview smoke
```

Do not migrate a healthy repository to another runner solely for Organization uniformity.

## 4. Mira Cloud test profile

New TypeScript Cloudflare Worker services should default to:

- Vitest 4.1+;
- `@cloudflare/vitest-plugin`;
- `wrangler types` as part of type verification;
- local Worker-runtime tests using the repository's Wrangler configuration;
- D1/R2/KV/Workflow/DO bindings tested in the Workers runtime when the service depends on them;
- outbound provider/API calls mocked at the network boundary for T1–T3;
- real provider/network calls reserved for explicit preview/E2E smoke where needed.

Cloud services should avoid treating Node-only mocks as sufficient evidence for Worker-runtime behavior.

For runtime integration tests, prefer exercising exported Worker handlers and real local bindings. Storage state must be isolated between tests unless a test explicitly verifies shared-state behavior.

## 5. CI and branch promotion gates

The canonical environment model remains:

```text
feat/* -> dev -> test -> prod
```

Testing gates map to it as follows.

### Feature PR → dev

Required by default:

- static/type/lint checks applicable to the repository;
- T1 Unit;
- T2 Contract for touched contracts;
- fast deterministic T3 Runtime integration for touched runtime behavior.

Large platform builds may run in parallel and may be repository-specific merge gates according to local policy.

### dev → test

Required by default:

- repository `check` green on the promoted commit;
- relevant full T3 integration suite;
- build/package/deployability evidence;
- T4 for journeys affected by the release when a deployable test/preview environment exists.

### test → prod

Required by default:

- exact candidate version/deployment identified;
- relevant T4 critical journeys green;
- rollback anchor captured;
- no unresolved release blocker.

### After prod deployment

Required:

- T5 production smoke against the exact deployed version;
- record deployment/release/version evidence;
- rollback when a release-critical smoke fails and recovery is not immediately proven safe.

## 6. Test evidence

A meaningful test result should identify, where applicable:

- repository;
- commit SHA;
- test layer (`T1`–`T5`);
- command/workflow;
- environment/runtime;
- result;
- deployment/version/release ID for T4/T5;
- known skipped or conditional coverage.

CI status is execution evidence. Issues/PRs may summarize it, but must not claim a test passed before the actual run completed.

Control Room and other management surfaces should project this evidence rather than invent a second test status.

## 7. Test data and external services

- Never use production user data as ordinary test fixtures.
- Prefer deterministic fixtures and disposable test identities/resources.
- Secrets are never committed as fixtures.
- External AI/provider calls should not be required for ordinary unit/contract CI.
- Tests that consume paid APIs, send messages, write external Destinations, or mutate real infrastructure must be explicit T4/T5 operations and visibly scoped.
- Idempotency/retry behavior must be tested for any workflow that can be retried after a partial external side effect.

## 8. Coverage policy

Organization policy does not impose a global line-coverage percentage.

Coverage percentage is a diagnostic, not an acceptance target. Repositories may set local thresholds where useful, but merge/release confidence should primarily come from meaningful contract, runtime, and critical-journey coverage.

A changed critical contract with no targeted test is higher risk than a high global coverage number.

## 9. Exceptions

A repository may diverge from this standard when its platform requires another approach. The exception must be documented locally with:

- which layer/command differs;
- why;
- what evidence replaces it.

Do not silently redefine Organization-level test semantics inside a repository.
