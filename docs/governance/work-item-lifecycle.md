# Work Item Lifecycle

Status: active Organization guidance.

This document defines the lifecycle position of Mira engineering work items. The model is intentionally small: one GitHub Issue contract, one native Project `Status`, and separate evidence/environment systems that keep their own meanings.

Use [`../../skills/create-work-item/SKILL.md`](../../skills/create-work-item/SKILL.md) for Issue creation procedure and authority checks. Use [`../../skills/close-work-item/SKILL.md`](../../skills/close-work-item/SKILL.md) for acceptance, closure, decline, duplicate, and reopen procedure.

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

Issue creation requires explicit creation authority. Discussion, review findings, audit findings, TODO discovery, or a recommendation that something should be tracked do not authorize autonomous Issue creation.

Normal Organization intake adds open Issues to `Mira Development`. Current live Project behavior assigns newly added items native `Status=Todo`.

The creator should not duplicate Status, Priority, Effort, dates, assignees, linked PRs, or similar management/system metadata inside the Issue body.

Creating an Issue alone does not authorize implementation. Explicit execution authorization may be given separately or in the same maintainer instruction.

## 5. Starting work

When implementation or other substantive execution is explicitly authorized:

1. keep the Issue open;
2. move Project `Status` to `In Progress` when Project mutation capability is available;
3. when a repository work branch is needed and the repository supports Mira Start Work, create it through the trusted start-work path as a GitHub-native linked branch from the correct environment base;
4. perform the work under the Issue, repository, testing, review, and environment contracts.

The linked-branch step is part of normal work-start plumbing, not a separate maintainer chore. The automation may use the Issue number in its generated branch name as a lookup hint, but the branch name itself is not proof of the Issue contract. Consumers such as AI Review must verify the relation from GitHub server-side linked-branch data.

Do not infer `In Progress` merely from a branch name, PR existence, commit, CI run, timestamp, or comment activity.

If the current execution tool cannot mutate Project Status, do not invent a substitute field or prose status. Authorized technical work may continue; report the management-projection gap when it matters and repair the Project projection when a capable path is available.

## 6. Blocked work

`Blocked` is a condition, not a fourth lifecycle state.

Record the blocker on the Issue, using GitHub issue dependencies when another Issue is the actual dependency and concise Issue context when the blocker is external.

- If the work remains actively owned while the blocker is being resolved, keep `In Progress`.
- If the maintainer deliberately pauses/dequeues the work, move it to `Todo`.

Do not create a parallel `Blocked` lifecycle column merely to make the board more descriptive.

A blocked or stale Issue must not be closed as `not_planned` unless that outcome has been explicitly decided.

## 7. Pull requests, review, and verification

For the standard Mira branch model, a normal implementation PR should inherit its authoritative work-item relation from the GitHub-native linked branch created at work start. This server-side relation is the preferred trusted Task source for Organization AI Review on non-default development branches.

PR prose such as `Refs #123`, `Closes #123`, a title reference, or any other PR-controlled text may remain useful for humans, but it is not by itself a trusted Task contract. Legacy or manually created branches may use an explicit GitHub server-side relation as a compatibility path; do not fall back to trusting PR text merely because the native linked-branch relation is absent.

Do not rely on `Closes` / `Fixes` in a feature PR to mean that the Issue contract has been accepted. Mira commonly merges feature work into non-default `dev`, and acceptance may require evidence beyond merge.

A PR merge, AI review verdict, human review, `Mira Gate`, test run, build, device check, deployment, or smoke result is evidence. It becomes acceptance evidence only to the extent required by the current Issue contract.

Evidence does not grant acceptance authority. While required verification or acceptance is unresolved, keep the Issue open. If the work remains actively being carried through, its Project Status remains `In Progress`.

## 8. Environment promotion

Project Status does not encode `dev`, `test`, or `prod`.

If the Issue acceptance criteria require test- or production-environment evidence, keep that Issue open until the required evidence exists.

If promotion/release is an independently verifiable outcome owned by a separate work item, the implementation Issue may close once its own contract is accepted. Do not keep feature Issues artificially alive merely to duplicate another release work item.

Closing an implementation Issue does not authorize promotion or release unless that authority is separately granted.

## 9. Acceptance and closure

Acceptance is a distinct authority decision against the Issue contract. Closing is a result mutation, not an automatic consequence of implementation or verification.

Follow [`../../skills/close-work-item/SKILL.md`](../../skills/close-work-item/SKILL.md) before mutating Issue state or close reason.

For an authorized `completed` outcome:

1. verify the exact acceptance criteria against current evidence;
2. identify any explicit exceptions or accepted validation gaps;
3. record the material evidence/decision on the Issue or linked PR when useful for audit;
4. close the Issue with `state_reason=completed`.

Current live Project behavior moves a closed Issue to native `Status=Done`; do not add a second completion reconciler when the native workflow already owns that edge.

An implementing AI may self-accept only when the maintainer explicitly authorizes self-acceptance and objective, proportionate evidence can decide the criteria. Self-acceptance must be identified as delivery/self-acceptance, not independent review.

If evidence is complete but acceptance/closure authority is absent, keep the Issue open and report that the contract appears ready for an authorized acceptance decision.

For work intentionally abandoned or superseded, use `not_planned` or `duplicate` only when that outcome is explicitly authorized and supported. Project `Done` still means the item is inactive; the Issue close reason explains why.

## 10. Reopening

Reopening is an outcome mutation and requires explicit reopen authority. It does not by itself authorize resumed implementation.

Current live Project behavior does not repair the reopen edge automatically: an Issue can be `open` with `state_reason=reopened` while its Project Status remains `Done`.

When an Issue is reopened:

1. update its contract if scope/acceptance changed materially;
2. restore Project Status to `Todo` by default;
3. if the same maintainer instruction explicitly authorizes immediate resumed execution, use `In Progress` instead.

Organization automation may repair only the unambiguous stale projection `open + state_reason=reopened + Status=Done -> Status=Todo`. That repair follows explicit GitHub state; it must not infer broader lifecycle intent.

## 11. Compatibility and migration

Work items created or started under the 2026-09 transition hold keep their existing Issue/PR/repository contracts. Normalization changes management projection only; it does not rewrite their scope, acceptance criteria, review conclusions, CI evidence, or environment state.

Do not seed native Status by mechanically translating legacy Stage values. Repair only states supported by current authoritative evidence. The legacy `Stage` field has been retired after verified cutover; do not recreate it as a compatibility layer.
