# External Worker Candidate Recovery

Status: active Organization guidance for AGT-059.

Candidate Recovery lets a later Worker run reuse the latest trustworthy Candidate for the same GitHub Issue without creating a second task database. The GitHub Issue remains the work contract and outcome source of truth; GitHub Actions run/artifact state remains execution evidence.

## Recovery index

Each run that leaves a durable Candidate publishes one machine-readable pointer as a GitHub Actions bot comment on the owning Issue:

```text
<!-- mira-recovery-candidate:v1
{...json...}
-->
```

The pointer is an index only. It records run/artifact identity, exact base, Candidate patch/tree identity, contract fingerprint, ambiguity guard, Verify state and Delivery state. Recovery must still download and validate the underlying Candidate/evidence before reuse.

Only pointers authored by `github-actions[bot]` are trusted. User-authored comments that imitate the marker are ignored.

Keeping the pointer on the original Issue is deliberate: if an Actions Artifact later expires, a subsequent run can distinguish “historical Candidate existed but is no longer recoverable” from “no prior Candidate ever existed.”

## Deterministic contract fingerprint

Recovery compatibility uses `.github/scripts/worker-candidate/recovery.py fingerprint`.

The canonical fingerprint contains:

- Issue number;
- normalized Issue title;
- normalized Issue body;
- eligible trusted maintainer contract amendments.

Normalization converts CRLF/CR to LF, removes trailing whitespace per line, and trims leading/trailing blank lines.

Trusted maintainer comments are already filtered by the Worker Enrollment boundary to human authors with current repository `write`, `maintain`, or `admin` permission.

A comment is deterministically classified as an amendment when it has the marker:

```text
<!-- mira-contract-amendment:v1 -->
```

or begins with an explicit supported amendment prefix such as `Contract amendment:`, `Scope change:`, `合同修订：`, `范围变更：`, or `返工要求：`.

Pure status/evidence comments may use:

```text
<!-- mira-contract-note:v1 -->
```

or a supported status/evidence prefix such as `Status:`, `Progress:`, `Evidence:`, `状态：`, `进展：`, or `证据：`.

Comments that cannot be classified deterministically do not silently disappear. Their normalized content is hashed into a separate `ambiguity_guard`. Recovery requires both the contract fingerprint and ambiguity guard to match the prior pointer. Therefore an ambiguous trusted comment may conservatively prevent Candidate reuse, but it cannot silently authorize reuse under a potentially changed contract.

## Recovery states

The machine state distinguishes:

- `fresh` — no prior trusted Candidate pointer exists;
- `recoverable` — same contract, Candidate identity valid, prior Candidate restored for continued Worker execution;
- `contract_drift` — prior Candidate exists but current contract fingerprint/ambiguity guard differs; old Candidate is not restored and the Worker starts from the current explicit base with drift recorded;
- `recovery_failed` — prior history exists but Artifact/evidence/identity/base restoration cannot be trusted; model execution is blocked;
- `delivery_retry_only` — prior Verify passed for the exact Candidate but Delivery did not complete; Worker/provider setup and Verify are skipped and only trusted Delivery is retried;
- `delivery_complete` — prior Candidate is already recorded as successfully delivered; the new run stops rather than creating duplicate work.

## Exact-base and advanced-base behavior

Every Candidate remains bound to its original exact `base_sha`.

For same-base continuation, Recovery performs the normal Candidate restore contract and then hands the restored workspace to the next Worker.

When the explicit delivery base has advanced:

1. Recovery first proves that the historical Candidate still reconstructs exactly on its original base.
2. The prior base must be an ancestor of the current explicit base.
3. Recovery attempts a deterministic Git `apply --3way --index` of the validated Candidate patch onto the current base.
4. A clean three-way application becomes `recoverable` with `base_strategy=base_advanced_clean_3way`.
5. Any conflict becomes `recovery_failed` with `base_strategy=conflict_fail_closed`; the workspace is reset to the current base and the model is not started.
6. A diverged/unavailable prior base also fails closed.

Recovery never silently rebases a conflicting Candidate.

## Verification-failure continuation

If the prior Candidate reached Verify and Verify failed, the next Worker receives:

- the restored Candidate workspace;
- source run/base/recovery state;
- the prior trusted verification result/log when available;
- instructions to address that evidence first rather than redoing unrelated discovery.

Prior Worker narration remains diagnostic only and never becomes trusted PASS evidence.

## Delivery-only retry

When prior Verify evidence says PASS for the same Candidate identity and Delivery is incomplete/failed:

- provider resolution is skipped;
- OpenCode installation is skipped;
- model execution is skipped;
- a fresh Verify is skipped;
- the prior Candidate and trusted Verify evidence are downloaded, revalidated, and re-published into the new run;
- Delivery restores the exact verified Candidate again and retries only Git branch/commit/Draft-PR delivery.

This makes transient GitHub Delivery failure independent from model cost.

## Retention and unavailable history

Candidate/Verify/Delivery Actions Artifacts currently have bounded retention. The Issue Recovery pointer persists independently.

If the pointer exists but a required Candidate or trusted Verify Artifact is expired/deleted/unavailable, Recovery records `recovery_failed` with an explicit unavailable/expired reason. It must not degrade that history into `fresh`.

## Permissions and caller rollout

AGT-059 adds two permissions to the future caller contract:

- `actions: read` so trusted Enrollment can download prior-run Candidate/Verify artifacts;
- `issues: write` so the isolated `recovery_index` job can publish the durable pointer.

The model step does not receive these GitHub capabilities. `recovery_index` has no contents or pull-request write authority.

Existing Mira product callers and the free-worker wrapper remain pinned to historical immutable engine SHAs until an explicit reviewed repin. Merging AGT-059 into the canonical Organization workflow must not silently change their runtime permissions or engine.

## Authority boundary

Recovery may preserve, restore, continue, verify, or retry Delivery for an already-authorized Issue. It does not grant authority to:

- merge;
- accept/close/reopen the Issue;
- release;
- deploy;
- promote environments;
- resolve product/architecture decisions outside the Issue contract.

The Recovery pointer is a projection/index, not a second lifecycle or outcome field.
