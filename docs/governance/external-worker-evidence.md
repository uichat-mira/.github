# External Worker evidence package

Status: active Organization guidance.

Lifecycle and role semantics are owned by [`../engineering/external-worker-lifecycle.md`](../engineering/external-worker-lifecycle.md). This document owns only the bounded evidence/artifact contract and must not redefine the Worker lifecycle.

The Mira External Worker emits bounded, role-specific evidence artifacts across Worker/Capture, Verify, Delivery, and Recovery. These artifacts complement GitHub Actions logs; they do not replace the GitHub Issue, Candidate, branch, commit, pull request, or Actions run as the durable engineering ledger.

## Package

AGT-058 separates evidence by execution boundary:

### Worker/Capture evidence

The `mira-external-worker-<run_id>` Artifact contains bounded Worker/Capture evidence such as:

- `worker-run.json` — Worker/Capture run identity, provider/model route, stage outcomes (including Candidate/Verify evidence re-publication on Delivery-only retry), Recovery mode/source, Candidate pointer/recoverability and permission metadata;
- `identity.txt`, `issue.json`, trusted-maintainer comment snapshot and `provider-route.json` — durable handoff inputs needed by later trusted stages;
- `contract.json`, `validation-contract.json`, `recovery-state.json`, Recovery context and discovered pointer metadata when applicable;
- metadata-only trajectory/session summary;
- bounded Worker output;
- `candidate-status.json` plus bounded Candidate capture stdout/stderr;
- changed-file / Candidate diff summaries.

The recoverable `candidate.patch` and `candidate.json` remain in a **separate immutable Candidate Artifact** named for run/attempt.

### Verify evidence

The `mira-external-worker-verify-<run_id>-<attempt>` Artifact records:

- `verify-run.json` — exact base, Candidate patch/tree identity, clean restore result, structured Validation result and read-only permission contract;
- `validation-report.json` — profile/legacy mode, tier ceiling, ordered checks, duration/status, explicit gaps and one of `PASS / REPAIR / BLOCKED / VALIDATION_GAP`;
- bounded `validation.log`; `verification.log` remains a compatibility alias for Recovery handoff during migration;
- Candidate restore result and bounded verification metadata when available.

Verify evidence is tied to the exact Candidate identity. Only `PASS` produces a successful Verify terminal status and can authorize ordinary Delivery. It does not contain provider credentials and has no GitHub mutation authority.

The Validation Profile schema and result semantics are owned by [`../engineering/external-worker-validation.md`](../engineering/external-worker-validation.md); this evidence document only defines what is persisted.

### Delivery evidence

The `mira-external-worker-delivery-<run_id>-<attempt>` Artifact records:

- `delivery-run.json` — restored Candidate identity, commit/push/Draft-PR stages, commit SHA, PR URL and Delivery authority boundary;
- Delivery restore result when available.

Delivery evidence exists independently of Worker model execution. A Delivery failure after Verify PASS therefore does not require the model to run again. The evidence is identity-checked before retry; missing evidence after a Delivery attempt fails closed because partial push/PR side effects may already exist.

Exact filenames remain implementation detail. The durable contract is that evidence is machine-readable, bounded, attributable to one immutable run/Candidate identity, and reflects the actual job boundary that produced it.

## Worker time budget

The reusable workflow's `timeout_minutes` input is a 60-minute advisory planning budget, not a hard job or step timeout. A Worker is not terminated merely because the budget elapses. GitHub-hosted runner platform limits remain an external ceiling and are explicitly outside the recovery guarantee.

## Provider/model identity

`worker-run.json` records both the requested and the effective provider, provider profile, model, and model route for the run. When a provider/profile route is selected it also records the frozen provider-registry revision and resolved registry SHA. Provider/model selection is run-scoped and does not mutate persistent OpenCode configuration; see [`external-worker-provider-model.md`](external-worker-provider-model.md).

## Trust boundary

The evidence package distinguishes two classes of activity:

1. model-owned repository reasoning/edit activity, represented by the OpenCode session-derived metadata trajectory and bounded Worker output;
2. trusted workflow-owned Capture, clean-room Verify, and Delivery activity, represented by separate role-specific Actions jobs and evidence artifacts.

A model session cannot grant itself merge, Issue outcome, release, deployment, promotion, or broader workflow authority.

## OpenCode integration

Use OpenCode's supported session/export surface rather than wrapping or reimplementing the agent loop.

The Worker:

1. snapshots visible session IDs before model execution;
2. runs the pinned OpenCode session;
3. resolves the newly created session when possible;
4. requests a sanitized native JSON export;
5. extracts only metadata needed for audit/recovery;
6. deletes the intermediate sanitized export before artifact upload.

If a sanitized structured export is unavailable, the package records that limitation explicitly instead of persisting an unsanitized transcript.

## Secret and size safety

Persisted evidence must not contain provider credentials, GitHub tokens, environment dumps, private reasoning text, raw prompt bodies, or unbounded tool inputs/results.

Current bounds:

- Worker persisted output: 120 KB maximum.
- Trusted Verify persisted output: 120 KB maximum.
- Session-derived trajectory: 500 events maximum.
- Diagnostic Actions artifact retention: 14 days.
- Candidate Actions artifact retention: 14 days in the current AGT-057 implementation. This is an implementation retention window, not a promise of permanent recovery storage.

Truncation is explicit in companion metadata rather than silently dropping content.

## Recovery pointer

AGT-059 publishes a machine-readable `github-actions[bot]` comment on the owning Issue for each durable Candidate. The comment points to the pointer run and Candidate-origin run, Candidate Artifact ID/digest, exact base/base branch, deterministic Worker branch, contract fingerprint/ambiguity guard, exact Candidate digest/tree identity, Verify state and Delivery state. It is an index/projection only; underlying Artifacts and Git state remain the facts to validate.

Because the pointer persists after Artifact retention expires, later runs can report historical-but-unavailable Recovery state instead of pretending no previous work existed.

Pointer selection follows Candidate-origin run ID/attempt, so a delayed Delivery retry cannot supersede a newer Candidate merely by publishing later. A malformed newest bot-authored Recovery marker fails closed. An already delivered Candidate returns its original branch and Draft PR URL as a successful no-op, without publishing another pointer.

## Failure semantics

AGT-058 no longer compresses the entire pipeline into one terminal status. The Actions job graph and role-specific evidence distinguish:

- **Worker/Capture failure** — no Verify or Delivery is authorized; a successfully uploaded Candidate may still be recoverable.
- **Verify non-PASS** — Candidate and Verify/Validation evidence remain; `REPAIR`, `BLOCKED`, and `VALIDATION_GAP` all prevent Delivery while preserving their distinct structured result.
- **Delivery failure** — Verify already passed for the same Candidate identity; the next run may enter `delivery_retry_only`, reusing trusted Verify evidence without provider/model execution. Branch and Draft PR delivery are idempotent: an exact existing Candidate branch/PR is reused, while mismatched existing state fails closed.
- **Delivery-only retry** — Candidate and Verify evidence re-publication outcomes are recorded separately; Delivery is allowed only when both re-publications succeeded.
- **Already delivered** — a later dispatch returns the previously verified branch/PR identity without creating a new branch, rerunning Verify, or creating another PR.
- **Success** — Delivery commit tree is mechanically equal to the verified Candidate tree and the resulting PR is Draft against the explicit delivery base.

A local patch is never considered recoverable until its Candidate Artifact upload succeeds. A Candidate is never considered verified merely because Worker self-tests passed. A verified Candidate is never considered delivered merely because Verify passed.

## Source of truth

Evidence is diagnostic and audit material.

- the GitHub Issue owns the work-item contract and outcome;
- repository/workflow/runtime state owns current technical reality;
- the Actions run owns execution-state evidence;
- branch/commit/PR state owns Git delivery evidence;
- this package provides a bounded reconstruction aid for one Worker run.

Do not turn the package into a second task ledger, monitoring database, retry controller, or permanent transcript store.
