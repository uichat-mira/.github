---
name: execute-work-item
description: Execute one explicitly authorized Mira Organization engineering work item from its current GitHub Issue contract, making the smallest coherent change and returning concrete verification evidence without accepting or closing the work item.
---

# Execute Work Item

Use this Skill when an implementation agent has been explicitly authorized to execute **one** existing engineering work item in a repository under `uichat-mira`.

This Skill defines the reusable execution loop. It does **not** replace the current Organization `AGENTS.md`, repository-local `AGENTS.md`, the GitHub Issue contract, repository tooling, or review/acceptance policy.

## Preconditions

Before editing:

1. retrieve and follow the current `uichat-mira/.github/AGENTS.md` from `main`;
2. read the target repository's current root `AGENTS.md` and any more specific instructions that apply;
3. read the exact GitHub Issue / task contract assigned to this run;
4. inspect the actual code, configuration, tests, and active documentation needed to verify current technical reality;
5. identify the target outcome, allowed scope, explicit non-goals, acceptance criteria, and required evidence.

If the assigned work item is missing, ambiguous, already closed, materially conflicts with current instructions, or requires a maintainer decision that the contract does not make, stop and report the blocker. Do not invent scope to keep moving.

## Authority boundary

Execution authority is not outcome authority.

Unless the current maintainer instruction or task contract explicitly grants additional authority, do not:

- create unrelated Issues or expand the work into adjacent cards;
- accept, close, decline, duplicate, or reopen the Issue;
- merge a pull request;
- promote environments or publish a release;
- weaken repository protections, CI, tests, or review gates;
- perform a high-risk operation that repository instructions reserve for maintainer confirmation.

A worker may gather and report evidence without having authority to accept the result.

## Execution loop

### 1. Establish the smallest coherent change

Use the Issue outcome and current code to choose the minimum implementation that satisfies the contract.

- Preserve public/runtime/state/persistence/security boundaries unless the Issue explicitly changes them.
- Prefer an existing local pattern over a new abstraction when both satisfy the contract.
- Do not attach opportunistic cleanup, dependency upgrades, style rewrites, or speculative infrastructure.
- Do not add silent fallback, compatibility behavior, mocks, disabled checks, or hardcoded local values just to make verification green.

If implementing the accepted outcome would require a materially larger architectural or product decision, stop and surface that decision instead of smuggling it into the patch.

### 2. Implement in bounded steps

Keep each edit reviewable and reversible. Re-read nearby types, tests, configuration, and source-adjacent docs before changing a boundary.

When a deterministic defect is being fixed, add proportionate regression evidence when practical.

Never modify files that the repository contract marks forbidden. Treat generated files according to their owning generator rather than editing them by hand.

### 3. Verify with the lowest sufficient evidence

Run the cheapest reliable checks that can actually prove the acceptance criteria.

- Test behavior and contracts, not incidental implementation shape.
- Do not claim an unexecuted test, build, smoke, deployment, or device check as passed.
- Do not turn a failing check green by skipping, deleting, weakening, or broadening mocks around the subject under test.
- If required evidence cannot run in the current environment, record the exact validation gap.

A passing lower-level test is not evidence for a higher-level behavior it cannot prove.

### 4. Leave a recoverable handoff

Before ending the run, leave enough durable evidence that another fresh agent can continue without relying on chat memory.

Report:

- what changed and why;
- exact files or surfaces changed;
- exact verification commands/checks and their results;
- remaining failures, blockers, risks, or intentionally deferred validation;
- any maintainer/product decision still required.

Prefer durable repository, commit, pull-request, review, test, and CI evidence over narrative state kept only in the model session.

## Completion boundary

Implementation is complete only when the current work-item outcome can be evaluated from concrete evidence.

If the implementation is ready for review, hand it off for review according to the repository's delivery workflow. Do not represent self-verification as independent review or Issue acceptance.

If the task cannot be completed safely within its current contract, stop with a precise blocker rather than broadening the contract autonomously.
