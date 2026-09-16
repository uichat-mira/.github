---
name: close-work-item
description: Verify, accept, close, decline, duplicate, or reopen Mira Organization work items without inferring outcome authority from implementation evidence.
---

# Close Work Item

Use this Skill when a maintainer explicitly asks to verify for acceptance, accept, close, decline, mark duplicate, or reopen a GitHub Issue work item under `uichat-mira`.

Closing or reopening an Issue changes the recorded work-item outcome. It is not a clerical side effect of implementation, merge, review, CI, deployment, or Project state.

## 1. Authority comes before outcome mutation

Before changing Issue state or close reason, establish that the current instruction or applicable contract explicitly grants the requested outcome authority.

Do **not** infer acceptance or closure authority from any of the following:

- the implementation appears finished;
- a pull request merged;
- review returned no blocking findings;
- CI, tests, build, deployment, or smoke checks passed;
- Project `Status` looks ready or stale;
- all acceptance criteria appear objectively satisfied;
- the same AI implemented the work;
- a previous conversation discussed closing later.

A single maintainer instruction may grant several actions at once. For example, `做完后按验收标准自验收并关闭` grants implementation, acceptance, and closure authority in one instruction. Do not require a ceremonial second confirmation when authority is already explicit.

If authority is missing, gather or summarize evidence if that is within scope, keep the Issue open, and report that acceptance/closure remains a maintainer decision.

## 2. Re-read the current contract

Before deciding an outcome:

1. retrieve current Organization `AGENTS.md`;
2. read the target repository's applicable instructions;
3. read the current Issue body and material contract-changing comments;
4. read [`../../docs/governance/work-item-lifecycle.md`](../../docs/governance/work-item-lifecycle.md);
5. inspect the exact evidence needed by the Issue acceptance criteria.

Do not accept against a remembered or earlier version of the Issue when its contract has changed.

## 3. Evidence and acceptance are separate

Evidence answers whether a criterion is supported. Acceptance is the authorized decision that the Issue contract is satisfied.

A merge, review, test, CI run, deployment, screenshot, device check, or smoke result proves only the claim that result actually establishes.

For every material acceptance criterion, identify concrete supporting evidence or an explicit validation gap. Do not silently waive a criterion because the rest of the work looks healthy.

If the implementing AI is explicitly authorized to self-accept, it may do so only when the criteria are objectively decidable from proportionate evidence. Record that this is **self-acceptance / delivery acceptance**, not independent review.

## 4. Choose the Issue outcome deliberately

### `completed`

Use `completed` only when:

- acceptance/closure authority is present; and
- the Issue acceptance criteria are satisfied by current evidence, or the authorized maintainer explicitly accepts a known validation gap.

Prefer recording a concise acceptance comment before closure when the evidence is not already obvious from the Issue/PR timeline.

### `not_planned`

Use `not_planned` only when the maintainer or applicable contract explicitly decides the work will not be completed under this Issue.

Do not convert a blocked, paused, difficult, stale, or low-priority Issue into `not_planned` merely because execution stopped.

### `duplicate`

Use `duplicate` only when the duplicate relationship is established and the owning replacement Issue is identifiable. Record or link the canonical work item when practical.

Do not mark two merely related work items as duplicates.

## 5. Closure procedure

For an authorized `completed` closure:

1. verify each acceptance criterion against current evidence;
2. identify any explicit exceptions or accepted validation gaps;
3. record the material acceptance decision/evidence when useful for audit;
4. close the Issue with `state_reason=completed`;
5. rely on native Project behavior to project the closed Issue as `Status=Done`;
6. repair Project Status only if observable evidence shows the projection is stale.

For `not_planned` or `duplicate`, record the outcome reason when useful, then close with the matching GitHub state reason. `Done` still means inactive; the Issue close reason owns the outcome semantics.

Do not manually maintain a second completion field, Stage, prose status, or environment alias.

## 6. Reopening

Reopening requires explicit reopen authority. Reopening alone does **not** authorize resumed implementation.

After reopening:

- default management position is `Todo`;
- if the same instruction explicitly authorizes immediate resumed execution, use `In Progress`;
- if native Project behavior leaves the reopened Issue at `Done`, Organization automation may repair the unambiguous stale projection back to `Todo`.

If scope or acceptance criteria changed materially, update the Issue contract rather than treating reopen as a hidden new task.

## 7. Stop conditions

Keep the Issue open and report the gap instead of guessing when:

- acceptance or closure authority is missing;
- the current Issue contract cannot be retrieved;
- a material acceptance criterion lacks required evidence;
- evidence belongs to a different version, branch, environment, device, or candidate;
- the intended close reason is ambiguous;
- a repository/Organization contract conflict changes the acceptance decision and precedence does not resolve it.

## Quality check

Before mutating Issue state, confirm:

- outcome authority is explicit;
- the current Issue contract was read;
- acceptance evidence matches the actual criteria;
- merge/review/CI was not mistaken for acceptance authority;
- `completed`, `not_planned`, or `duplicate` reflects the intended outcome;
- Project `Status` is treated as projection, not outcome truth;
- closure does not silently authorize release, promotion, or unrelated follow-up work.
