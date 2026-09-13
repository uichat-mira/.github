# Work Item Lifecycle

Status: trial guidance, introduced 2026-09-14.

This document defines how Mira Organization work items move after intake. It is intentionally small. The trial should run for several days before broader lifecycle automation is added.

## Responsibilities

Mira keeps these concepts separate:

- **GitHub Issue** — engineering work-item truth: goal, scope, acceptance criteria, evidence, decisions, and whether the work item remains open.
- **Stage** — Organization Issue Field used to express the work item's management lifecycle and surfaced as a column in `Mira Development`.
- **GitHub Project** — management projection over the Issue and its Organization fields.
- **Project Status** — not used as a second work-item lifecycle. Do not duplicate Stage in another Status field.

Closing an Issue and moving its Stage are related actions, but they are not the same state mutation.

## Stage model

The existing Organization Stage values are:

```text
Backlog -> Ready -> In Progress -> Blocked -> Verification -> Ready to Ship -> Done
```

Use them with these meanings:

- **Backlog** — the work item is captured but is not yet committed for execution.
- **Ready** — the work item is sufficiently defined and accepted for upcoming execution, but implementation has not started.
- **In Progress** — implementation or other substantive execution is underway.
- **Blocked** — progress cannot continue because of a material dependency, missing decision, external condition, or unavailable required capability. Record the blocker on the Issue.
- **Verification** — implementation is complete enough for the required checks, review, evidence gathering, or acceptance decision. The Issue remains open while acceptance is unresolved.
- **Ready to Ship** — the work-item contract has been accepted, but the same work item still requires an explicit promotion, deployment, release, or equivalent delivery step before it can be considered complete.
- **Done** — the work-item contract has been accepted and no further work remains under that Issue. `Done` does not imply production deployment unless production delivery was part of that Issue's acceptance contract.

The names form the Organization's standard lifecycle vocabulary, but real work does not need to pass mechanically through every value. For example, a blocked item may return to `In Progress`, and a small low-risk documentation task may move from `In Progress` directly to `Verification` and then `Done`.

## Normal completion order

For an accepted work item, use this order:

1. record the required implementation and verification evidence on the Issue and/or its linked PR;
2. decide acceptance against the Issue contract;
3. set `Stage = Done`;
4. close the Issue with `state_reason = completed`.

Do not report the work item as fully closed out while its management projection still says another lifecycle stage.

The Organization intake workflow may reconcile a `closed` Issue whose `state_reason` is `completed` to `Stage = Done` when ordering or tooling leaves Stage stale. That automation is a repair path, not a substitute for deliberate acceptance.

## Verification and self-acceptance

An implementing AI may perform acceptance only when the maintainer has explicitly authorized it and the Issue has objective, proportionate evidence that can decide the acceptance criteria. The acceptance record must distinguish self-acceptance from an independent review.

High-risk work, or work whose contract requires maintainer/independent acceptance, must not be self-accepted merely because implementation checks are green.

## Other closure reasons

`Done` means accepted completion. Do not force other closure reasons into `Done` merely to make the board look tidy.

- `not_planned`, duplicate, or equivalent non-completion closures may close the Issue without setting `Stage = Done`.
- If such work needs a different management presentation during the trial, preserve the last meaningful Stage rather than inventing a hidden cancellation lifecycle.

## Reopening

When completed work is reopened because additional work is genuinely required:

1. reopen the Issue;
2. move Stage from `Done` to the stage that reflects the real next state, usually `Backlog`, `Ready`, `In Progress`, or `Blocked`;
3. update the Issue contract when scope or acceptance criteria changed materially.

Do not leave a reopened Issue at `Done` while substantive work is pending.

## Trial automation boundary

During this trial, Organization automation may only manage these lifecycle defaults:

- open Issue with empty Stage -> `Backlog`;
- closed Issue with `state_reason = completed` -> `Done`.

Do **not** automatically infer `Ready`, `In Progress`, `Blocked`, `Verification`, or `Ready to Ship` from branch names, PR state, comments, timestamps, or other indirect signals. Those transitions remain explicit until real usage demonstrates a safe rule.