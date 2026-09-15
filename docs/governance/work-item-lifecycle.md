# Work Item Lifecycle

Status: **transition hold** since 2026-09-15.

The 2026-09-14 Stage-based lifecycle trial is suspended while Mira re-audits the full work-item model from Issue creation through implementation, review, verification, environment promotion, acceptance, closure, and reopen.

This hold exists to protect work that is already in flight. It is not the replacement lifecycle design.

## Active-work compatibility rule

Existing Issues and pull requests continue under the task, repository, review, testing, and environment contracts that applied when their work began.

Do not reinterpret an in-flight work item's acceptance criteria merely because the Organization lifecycle model is being redesigned.

During the hold:

- continue implementation, review, CI, testing, promotion, and evidence collection normally;
- keep the GitHub Issue as the work-item contract;
- keep repository/runtime reality authoritative for technical state;
- do **not** require an active thread to migrate lifecycle metadata before it can continue;
- do **not** mutate Organization Issue Field `Stage` or Project `Status` unless the maintainer explicitly requests that mutation for the specific work item;
- do **not** infer lifecycle transitions from PR merge, branch name, CI state, comments, timestamps, deployment state, or Issue close reason;
- do **not** repair old Stage/Status values merely to make the Project look tidy.

If lifecycle metadata is stale during the hold, leave it stale and rely on the Issue/PR/evidence until the replacement model is accepted.

## Project intake during the hold

Open Organization Issues may still be added automatically to `Mira Development` so work remains discoverable.

The intake workflow must not assign or reconcile `Stage` or `Status` while this hold is active.

## Acceptance and closure during the hold

Acceptance remains a separate authority decision governed by the current Issue contract and applicable repository/Organization verification rules.

An implementing AI may perform self-acceptance only when the maintainer explicitly authorizes it and objective evidence can decide the Issue acceptance criteria. Self-acceptance must not be presented as independent review.

When a maintainer authorizes acceptance or closure during the hold:

1. verify the exact Issue acceptance criteria against current evidence;
2. record the acceptance/evidence when useful for audit;
3. close or reopen the Issue only within that explicit authority;
4. leave `Stage` and Project `Status` unchanged unless the maintainer separately asks to mutate lifecycle metadata.

A PR merge is implementation evidence, not automatic Issue acceptance.

Environment promotion (`feat/* -> dev -> test -> prod`) remains governed by the environment/testing contracts and must not be inferred from lifecycle metadata.

## Historical Stage trial

The suspended trial introduced the following Stage vocabulary:

```text
Backlog -> Ready -> In Progress -> Blocked -> Verification -> Ready to Ship -> Done
```

It also introduced automation for:

- open Issue with empty Stage -> `Backlog`;
- closed Issue with `state_reason = completed` -> `Done`.

Those mutation rules are **no longer active policy** during this hold. Existing values are historical/project data only; do not treat them as instructions for new mutations.

The replacement lifecycle must be accepted separately after the Organization completes the end-to-end audit. Until then, avoid creating a second lifecycle or partially migrating cards.