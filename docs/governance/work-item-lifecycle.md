# Work Item Lifecycle

Status: active Organization guidance.

This document defines the lifecycle of Mira engineering work items. The model is intentionally small: one GitHub Issue contract, one native Project `Status`, and separate evidence/environment systems that keep their own meanings.

## 1. One lifecycle field

`Mira Development` uses GitHub Project's native `Status` as its only work-item lifecycle field:

```text
Todo -> In Progress -> Done
```

Do not create or maintain a second lifecycle in Organization Issue Fields, labels, Issue prose, PR text, CI state, or environment branches.

The former Organization Issue Field `Stage` and its values (`Backlog / Ready / In Progress / Blocked / Verification / Ready to Ship / Done`) are legacy migration data, not active lifecycle policy.

## 2. Ownership boundaries

Keep these concepts separate:

- **GitHub Issue** — work-item contract and outcome: goal, scope, acceptance criteria, decisions, evidence, open/closed state, and close reason.
- **Project `Status`** — coarse management position only: `Todo`, `In Progress`, or `Done`.
- **Organization Issue Fields** — structured cross-repository metadata such as Priority, Effort, Start date, and Target date.
- **Pull request / review / CI** — implementation and verification evidence. A merge or green check is not Issue acceptance by itself.
- **Environment model** — `feat/* -> dev -> test -> prod` describes code/environment position. It is not a Project lifecycle.

If these surfaces disagree, first identify which concept is stale. Do not make one surface impersonate another.

## 3. Status semantics

### Todo

The Issue is open but is not currently under active execution.

Typical cases include newly captured work, queued work, work waiting for an explicit start decision, or work that has been deliberately paused and returned to the queue.

`Todo` does **not** authorize implementation.

### In Progress

The Issue is open and substantive execution has been explicitly authorized and is underway.

An explicit maintainer instruction such as "开始施工", "继续做这张卡", or an equivalent unambiguous authorization may establish execution authority. If the same instruction both creates the Issue and explicitly authorizes implementation, a second ceremonial confirmation is not required.

Review, CI, local verification, acceptance preparation, and temporary blockers do not require extra lifecycle columns. The item normally remains `In Progress` while the same accepted work is actively being carried through.

If work is explicitly paused or returned to the queue, move it back to `Todo`.

### Done

The underlying Issue is closed and the work item is no longer active.

`Done` means **inactive**, not necessarily "successfully accepted". The Issue close reason carries the outcome:

- `completed` — accepted/finished work;
- `not_planned` — deliberately not completed;
- `duplicate` — superseded by another work item.

Do not create separate Project lifecycle states merely to restate close reasons that GitHub already records on the Issue.

## 4. Creation and intake

Creating a work item means creating the Issue contract in the repository that owns the work.

Normal Organization intake adds open Issues to `Mira Development`. Current live Project behavior assigns newly added items native `Status=Todo`.

The creator should not duplicate Status, Priority, Effort, dates, assignees, linked PRs, or similar management/system metadata inside the Issue body.

Creating an Issue alone does not authorize implementation. Explicit execution authorization may be given separately or in the same maintainer instruction.

## 5. Starting work

When implementation or other substantive execution is explicitly authorized:

1. keep the Issue open;
2. move Project `Status` to `In Progress` when Project mutation capability is available;
3. perform the work under the Issue, repository, testing, review, and environment contracts.

Do not infer `In Progress` merely from a branch name, PR existence, commit, CI run, timestamp, or comment activity.

If the current execution tool cannot mutate Project Status, do not invent a substitute field or prose status. Authorized technical work may continue; report the management-projection gap when it matters and repair the Project projection when a capable path is available.

## 6. Blocked work

`Blocked` is a condition, not a fourth lifecycle state.

Record the blocker on the Issue, using GitHub issue dependencies when another Issue is the actual dependency and concise Issue context when the blocker is external.

- If the work remains actively owned while the blocker is being resolved, keep `In Progress`.
- If the maintainer deliberately pauses/dequeues the work, move it to `Todo`.

Do not create a parallel `Blocked` lifecycle column merely to make the board more descriptive.

## 7. Pull requests, review, and verification

For the standard Mira branch model, an implementation PR normally references its work item without encoding acceptance into the merge action. Prefer a plain relation such as `Refs #123` for ordinary `feat/* -> dev` work.

Do not rely on `Closes` / `Fixes` in a feature PR to mean that the Issue contract has been accepted. Mira commonly merges feature work into non-default `dev`, and acceptance may require evidence beyond merge.

A PR merge, AI review verdict, human review, `Mira Gate`, test run, build, device check, deployment, or smoke result is evidence. It becomes acceptance evidence only to the extent required by the current Issue contract.

While required verification or acceptance is unresolved, keep the Issue open. If the work remains actively being carried through, its Project Status remains `In Progress`.

## 8. Environment promotion

Project Status does not encode `dev`, `test`, or `prod`.

If the Issue acceptance criteria require test- or production-environment evidence, keep that Issue open until the required evidence exists.

If promotion/release is an independently verifiable outcome owned by a separate work item, the implementation Issue may close once its own contract is accepted. Do not keep feature Issues artificially alive merely to duplicate another release work item.

## 9. Acceptance and closure

Acceptance is a distinct authority decision against the Issue contract.

For accepted work:

1. verify the exact acceptance criteria against current evidence;
2. record the material evidence/decision on the Issue or linked PR when useful for audit;
3. close the Issue with `state_reason=completed`.

Current live Project behavior moves a closed Issue to native `Status=Done`; do not add a second completion reconciler when the native workflow already owns that edge.

An implementing AI may self-accept only when the maintainer explicitly authorizes acceptance and objective, proportionate evidence can decide the criteria. Self-acceptance must not be presented as independent review.

For work intentionally abandoned or superseded, close with the appropriate non-completed reason. Project `Done` still means the item is inactive; the Issue close reason explains why.

## 10. Reopening

Reopening is the one lifecycle edge that current live Project behavior does not repair automatically: an Issue can be `open` with `state_reason=reopened` while its Project Status remains `Done`.

When an Issue is reopened:

1. reopen the Issue and update its contract if scope/acceptance changed materially;
2. restore Project Status to `Todo` by default;
3. if the maintainer explicitly authorizes immediate resumed execution, use `In Progress` instead.

Organization automation may repair only the unambiguous stale projection `open + state_reason=reopened + Status=Done -> Status=Todo`. That repair follows explicit GitHub state; it must not infer broader lifecycle intent.

## 11. Compatibility and migration

Work items created or started under the 2026-09 transition hold keep their existing Issue/PR/repository contracts. Normalization changes management projection only; it does not rewrite their scope, acceptance criteria, review conclusions, CI evidence, or environment state.

Do not seed native Status by mechanically translating legacy Stage values. Repair only states supported by current authoritative evidence. Once migration is verified, remove the legacy `Stage` field so humans and AIs see one lifecycle vocabulary.
