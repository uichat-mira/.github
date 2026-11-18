# External Worker Bounded Return-to-Worker

Status: active Organization contract for repairable Validation failures.

This document owns the **bounded Return-to-Worker state machine, repair context contract, Candidate generation semantics, and automatic repair limit** for Mira External Worker.

It does not redefine:

- work-item scope/outcome — GitHub Issue owns that;
- Validation tiers/results — [External Worker Validation Profiles](external-worker-validation.md);
- Candidate Artifact mechanics — executable Candidate helper + evidence contract;
- cross-run Candidate discovery — [External Worker Candidate Recovery](../governance/external-worker-recovery.md);
- telemetry transport — [号脉 / Reporter / Worker Workforce](how-am-i-reporter-workforce-v1.md).

Observable workflow/scripts remain the technical truth if this document drifts.

## 1. Core rule

A trusted Validation result of `REPAIR` is a request to continue work on the **same Issue and current Candidate**, not a reason to discard the Candidate or start unrelated discovery.

The model is not allowed to reinterpret every failure as repair:

- `PASS` → Candidate is `VERIFIED`;
- `REPAIR` → bounded Return-to-Worker;
- `BLOCKED` → stop automatic model execution;
- `VALIDATION_GAP` → stop automatic model execution and require maintainer/contract disposition;
- contract drift, identity mismatch, security/permission failure, corrupted Candidate/evidence or repair infrastructure failure → stop/fail closed;
- Verify PASS followed by Delivery failure → Delivery-only retry; no model rerun.

## 2. State machine

The current lifecycle is:

```text
WORKING
  |
  v
CANDIDATE_CAPTURED (repair_round=0)
  |
  v
VALIDATING
  |
  +-- PASS ------------------------------> VERIFIED -> DELIVERY
  |
  +-- BLOCKED / VALIDATION_GAP ----------> BLOCKED
  |
  +-- REPAIR
        |
        v
      RETURNED -> REPAIRING round 1
        |
        v
      CANDIDATE_CAPTURED (repair_round=1)
        |
        v
      VALIDATING
        |
        +-- PASS -------------------------> VERIFIED -> DELIVERY
        +-- BLOCKED / GAP ----------------> BLOCKED
        +-- REPAIR
              |
              v
            RETURNED -> REPAIRING round 2
              |
              v
            CANDIDATE_CAPTURED (repair_round=2)
              |
              v
            VALIDATING
              |
              +-- PASS -------------------> VERIFIED -> DELIVERY
              +-- BLOCKED / GAP ----------> BLOCKED
              +-- REPAIR -----------------> ESCALATED
```

There are exactly **two automatic repair Worker entries**. A third repair model call is not part of the workflow topology.

`ESCALATED` means automatic repair is exhausted and maintainer takeover is required. It does not accept, close, merge, release or deploy anything.

## 3. Why repair uses a fresh Worker Runner

Verify intentionally runs on a separate clean Runner after the original Worker/Capture Runner.

After that boundary, the original OpenCode process/session is no longer a safe durable execution boundary. Reusing conversational memory would also make model-local history a second task truth source.

Therefore current Return-to-Worker uses a **fresh Worker Runner inside the same workflow lifecycle**. It restores the rejected Candidate and receives trusted structured context. This is continuation of the same work item, not a fresh task.

Initial Worker and repair Workers execute the same trusted shared runtime:

```text
.github/scripts/worker-runtime/run-worker.sh
```

The repair workflow adds only Candidate restore, trusted repair-context construction and the next Candidate/Verify generation.

## 4. Candidate generations

Candidate manifest schema remains version 1 and adds a backward-compatible `repair_round` field:

- missing field on historical Candidate → interpreted as `0`;
- initial Candidate → `repair_round=0`;
- first repaired Candidate → `repair_round=1`;
- second repaired Candidate → `repair_round=2`.

Restore may require an exact expected repair round. A mismatched generation fails closed.

The current Candidate generation is selected once by the trusted `lifecycle_handoff` stage. Delivery, Recovery projection and Reporter consume that selected generation rather than independently guessing which Candidate is current.

If a repair Worker/infrastructure attempt fails before producing a new durable Candidate, the last durable Candidate remains current while lifecycle state becomes `BLOCKED`.

## 5. Repair context

A repair Worker receives a bounded `repair-context.json`, constructed by trusted workflow code.

It contains only allowlisted structured facts:

- original Issue number/title/body;
- eligible trusted maintainer amendments from Recovery's canonical `contract.json`;
- current Candidate identity: repository, run/attempt, repair round, base, contract fingerprint, patch/tree identity and provider/model provenance;
- trusted Validation result, selected profile/tier identity, failed check, ordered executed/skipped checks, exit status/duration/failure classification and explicit gaps;
- trusted Validation Artifact reference;
- current repair round;
- instructions to preserve correct work, address trusted failure first and continue the same Issue.

It does **not** contain:

- prior model private reasoning;
- raw model transcript;
- raw Validation logs;
- provider/GitHub/Reporter credentials;
- environment dumps;
- prior Worker narration as trusted PASS evidence.

Repository-owned Validation commands may appear as structured trusted check metadata so the Worker can reproduce the failing check without inventing a new validation contract.

## 6. Authority and isolation

Repair Worker has the same model-side authority boundary as initial Worker:

- read/edit ephemeral workspace;
- run permitted diagnostics/tests;
- no GitHub Issue/PR/merge/release/deploy mutation authority.

Each repaired Candidate is independently validated on a separate Verify Runner with no provider credential.

Only a trusted structured `PASS` can enter ordinary Delivery.

Reporter/号脉 remains post-stage and non-blocking; it never decides repair eligibility or Candidate truth.

## 7. Cross-run persistence

The Recovery pointer records the selected Candidate generation and lifecycle projection, including:

- `candidate_origin_repair_round`;
- `lifecycle_state`;
- `validation_result`;
- selected Candidate Artifact identity;
- selected Verify evidence;
- Delivery state.

Recovery selection orders Candidate generations within one origin run by repair round.

A later dispatch must not reset the automatic repair budget:

- prior `BLOCKED` → automatic model execution stays blocked;
- prior `ESCALATED` → remains escalated;
- a structured `REPAIR` on `repair_round=2` → escalated;
- contract drift → maintainer review, not automatic zero-start Worker;
- historical pre-AGT-068 Candidate with no repair field behaves as round 0.

## 8. Observability projection

The GitHub lifecycle/Candidate/Validation evidence is authoritative.

Reporter projects repair facts through the existing `haomai.telemetry.v1` event schema without requiring a collector deployment:

- `recovery.detected`, `stage=repair`, `outcome=returned`, fixed error code identifying round 1/2;
- `recovery.failed`, `stage=repair`, `outcome=blocked|escalated`;
- `candidate.captured` references the currently selected Candidate Artifact;
- `verify.passed` is emitted only for the selected lifecycle `VERIFIED` Candidate, never merely because the initial Verify job successfully produced a non-PASS report.

This is stage telemetry, not Live Reporter/heartbeat.

## 9. Explicit non-goals

This contract does not:

- add specialized AI repairers for individual error classes;
- permit a third automatic repair model call;
- keep full model chat history as durable task state;
- turn `BLOCKED` or `VALIDATION_GAP` into code repair;
- rerun a model for Delivery-only failure;
- authorize merge, Issue outcome, release, deployment or environment promotion;
- require an expensive L4/L5 check merely because repair occurred.

## Working rule

> Keep the Candidate, return trusted evidence, repair twice at most, then hand the problem to a maintainer instead of burning another model run.
