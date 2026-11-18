# External Worker Lifecycle

Status: active Organization engineering contract for the current External Worker lifecycle.

This document owns the **lifecycle and role-boundary vocabulary** for Mira External Worker. It is a navigation and semantic contract, not a second runtime implementation.

Current technical reality remains owned by:

- `.github/workflows/mira-external-worker.yml` and its pinned helper scripts;
- repository/runtime configuration actually used by the caller;
- GitHub Actions, Candidate Artifacts, branches, commits and pull requests produced by a real run.

If this document disagrees with observable workflow/runtime behavior, the workflow/runtime is the current fact and this document must be repaired.

## 1. Source-of-truth boundaries

Do not duplicate one decision across several documents.

| Concern | Owner |
| --- | --- |
| Work-item contract and outcome | GitHub Issue + eligible trusted maintainer amendments |
| Current executable pipeline | `.github/workflows/mira-external-worker.yml` and pinned scripts |
| Lifecycle / role semantics | This document |
| Test layers and promotion semantics | [Organization Testing Standard](testing-standard.md) |
| Validation Profile / tier / result contract | [External Worker Validation Profiles](external-worker-validation.md) |
| Evidence package / artifact boundaries | [External Worker Evidence Package](../governance/external-worker-evidence.md) |
| Candidate cross-run recovery | [External Worker Candidate Recovery](../governance/external-worker-recovery.md) |
| Provider/model route selection | [External Worker Provider and Model](../governance/external-worker-provider-model.md) |
| Reporter / 号脉 / Workforce extension | [号脉 / Reporter / Worker Workforce V1](how-am-i-reporter-workforce-v1.md) |
| Control Room / Factory TV projection | Control Room repository and its work items |
| Organization authority / collaboration policy | [Organization AGENTS.md](../../AGENTS.md) |

A downstream document may reference a lifecycle state, but must not silently redefine what that state means.

## 2. Current pipeline

The current reusable Worker is a GitHub-native delivery pipeline around one model-running Worker.

```text
GitHub Issue
  |
  v
logical enrollment + Recovery discovery
  |
  v
Worker / Capture
  |
  v
immutable Candidate Artifact
  |
  v
clean-room Verify
  |
  +-- failure --> recoverable evidence / later continuation
  |
  v
Delivery
  |
  v
Draft PR
  |
  v
Recovery index

trusted_reporter observes the trusted stage facts independently
and may publish bounded stage events to 号脉.
```

The physical GitHub Actions jobs currently include:

- `worker_capture`;
- `verify`;
- `delivery`;
- `recovery_index`;
- `trusted_reporter`.

Enrollment is currently a **logical boundary inside `worker_capture`**, not a separate GitHub Actions job. Do not describe it as physically isolated unless the workflow changes.

## 3. Roles

### Issue / trusted amendments

The Issue owns the work contract and outcome. Eligible trusted maintainer amendments may change the execution contract according to the current Organization Skill and workflow rules.

The Worker does not create a second task contract from its own narrative.

### Worker

The Worker is the model-running OpenCode process.

It may:

- inspect the authorized repository/work item;
- edit the ephemeral workspace;
- run development tests and diagnostics within its tool boundary;
- report blockers and validation gaps.

It does not own GitHub mutation or work-item outcome authority.

Its self-reported tests are施工 feedback, not trusted Verify evidence.

### Capture / Candidate

Capture is trusted workflow code operating after Worker activity on the same runner.

Its purpose is to freeze recoverable code state into an immutable Candidate identity before later trusted stages depend on it.

The exact Candidate manifest, artifact contents, retention and evidence fields are owned by the Evidence/Recovery contracts, not duplicated here.

A Candidate means **candidate code exists**. It does not mean the code is verified or delivered.

### Verify

Verify runs on a separate clean GitHub-hosted runner.

It restores the exact Candidate against its bound base and checks Candidate identity before running caller/repository-owned verification.

Verify supports two validation modes after Candidate identity:

- profile mode uses the repository-owned Validation Profile and a hard maximum tier;
- legacy mode preserves the caller's existing `verification_command` during migration.

The profile schema, fail-fast ladder, cost ceiling and `PASS / REPAIR / BLOCKED / VALIDATION_GAP` report contract are owned by [External Worker Validation Profiles](external-worker-validation.md).

A non-PASS result preserves evidence and prevents Delivery. It is not proof that useful Worker code disappeared.

### Delivery

Delivery is the ordinary GitHub write boundary.

Only after the exact Candidate has trusted Verify evidence may Delivery create/reuse the isolated branch, commit the exact verified tree, push it and create/reuse a Draft PR.

Delivery does not own merge, Issue acceptance/closure, environment promotion, release or deployment authority.

A Delivery failure after Verify PASS is a delivery problem, not a reason to rerun the model by default.

### Recovery index

Recovery publishes a durable pointer on the owning Issue and lets later runs distinguish fresh work, recoverable Candidate history, contract drift, recovery failure, delivery-only retry and already-delivered state.

The pointer is an index/projection. Candidate Artifacts, trusted evidence and Git state remain the facts that must be validated before reuse.

### Trusted Reporter

The current `trusted_reporter` is an independent post-stage observer.

It reads trusted GitHub/job/evidence facts and may emit bounded stage events. Reporter failure does not roll back Candidate, Verify or Delivery.

Current Reporter is **not Live Reporter**: it must not be described as a trustworthy in-run token/tool heartbeat unless a separately accepted live-observation contract proves that capability.

### Foreman / Workforce

Foreman/Workforce is an upper scheduling/control-plane concept. It is not another implementation agent inside the reusable Worker.

It may eventually consume GitHub/Recovery/validation facts to decide eligibility, continuation, routing and escalation.

It must not create a second Issue/Run ledger or redefine the Worker lifecycle.

## 4. Current failure semantics

Current pipeline behavior distinguishes at least:

- Worker/Capture failure;
- Verify failure;
- Delivery failure;
- recovery failure;
- delivery-only retry;
- already delivered;
- successful Draft PR delivery.

The detailed evidence and Recovery rules are owned by the linked Evidence and Recovery documents.

Two important invariants:

1. `Worker failed` does not automatically mean `work lost` when a durable Candidate exists.
2. `Verify passed` does not mean `delivered`; Delivery is a separate boundary.

## 5. Time budget

`timeout_minutes` is currently an advisory Worker planning budget. It is not used as the normal hard termination deadline for the model-running step.

GitHub-hosted runner/platform ceilings remain external limits and are outside the normal Candidate recovery guarantee.

Do not reintroduce 30/45/60-minute values as a universal "kill the Worker" policy without a new contract and evidence.

## 6. Planned extensions — not current runtime

The following approved work items describe future behavior. They must not be written as already implemented until their acceptance evidence exists.

### AGT-068 — Return-to-Worker

[AGT-068](https://github.com/uichat-mira/.github/issues/85) owns the planned bounded Return-to-Worker repair loop.

Until it lands, a Verify failure can be recovered by a later dispatch using Candidate + trusted verification evidence, but the current reusable workflow does not automatically return the rejected Candidate to a Worker inside one repair lifecycle.

### OPS-032 — Factory TV real projection

[OPS-032](https://github.com/uichat-mira/control-room/issues/77) owns the real Control Room / Factory TV projection of Worker lifecycle, Validation and repair states.

Factory TV's current UI/demo data must not be described as live telemetry.

### Live Reporter

True in-run Live Reporter remains a separately accepted extension. Stage Reporter facts must not be relabeled as heartbeat/tool-stream evidence.

## 7. Historical design note

[PR #69](https://github.com/uichat-mira/.github/pull/69) recorded the original Worker v2 design proposal before Candidate, clean-room Verify, Delivery, Recovery and Trusted Reporter evolved into the current main-branch workflow.

It remains useful historical design context, but it is **superseded as a description of current runtime architecture** by:

1. observable workflow/runtime behavior;
2. this lifecycle contract;
3. the specialized owner documents linked above.

Do not copy unresolved or pre-implementation assumptions from PR #69 back into current guidance without re-verifying them against current code and work-item contracts.

## Working rule

> The model is the Worker, not the system. GitHub owns the engineering ledger; Candidate carries code state; trusted stages verify and deliver it; Recovery preserves continuity; Reporter and Control Room project facts without becoming facts themselves.
