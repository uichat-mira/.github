---
name: create-work-item
description: Create small, independently verifiable Mira Organization engineering work items as GitHub Issues while preserving the Organization source-of-truth model.
---

# Create Work Item

Use this Skill when a maintainer asks to create, split, formalize, or record an engineering task for a repository under `uichat-mira`.

The output is a **GitHub Issue work-item contract**. It is not a second ledger, an implementation plan pretending to be a contract, or a Project lifecycle update.

## Core principles

Every work item must satisfy both rules:

1. **Independently verifiable** — concrete evidence can decide whether the outcome is accepted.
2. **Small and fast** — prefer the smallest coherent change that can be implemented, reviewed, verified, and reverted without dragging unrelated work with it.

Small does not mean artificially fragmented. Keep changes together when they form one atomic behavior and cannot be meaningfully accepted separately.

## Sources of truth

Before creating a work item, follow [`../../docs/governance/source-of-truth.md`](../../docs/governance/source-of-truth.md):

- repository / workflow / runtime state is authoritative for current technical reality;
- GitHub Issue owns the work-item contract and outcome;
- Organization Issue Fields own structured planning metadata;
- GitHub Project `Status` is the management workflow projection;
- Organization and repository docs define policy and procedure;
- PR/review/CI provide implementation and verification evidence;
- public website content is a public projection.

Do not make an outdated document or Project value override observable technical reality.

When a newer explicit maintainer decision conflicts with written guidance, surface and resolve the conflict rather than silently choosing whichever interpretation is convenient.

## Procedure

### 1. Identify the owning repository

Determine which repository owns the behavior, contract, runtime, documentation, or infrastructure being changed.

Use current repository reality rather than naming guesses. Read relevant repository-local `AGENTS.md`, policy/docs, active contracts, and branch rules when they materially affect scope or verification.

For work spanning repositories, split only when there are distinct independently implementable and verifiable outcomes. Cross-link separate work items and identify the contract owner when useful.

### 2. Check for existing work

Before creating a new Issue, search the owning repository and, when useful, the Organization for:

- the same outcome;
- the same defect or symptom;
- the same contract change;
- an active parent or child work item that already owns the scope.

If an existing Issue already owns the outcome, use or update it instead of creating a duplicate.

### 3. Decide whether the work item is small enough

Split the work before creation when one proposed Issue contains outcomes that can be accepted independently, especially when they involve:

- unrelated product behaviors;
- different owning repositories with separate delivery paths;
- independent high-risk changes;
- separate deployment or migration checkpoints;
- different verification chains that can pass or fail independently.

Keep one Issue when the changes are tightly coupled and one acceptance decision naturally covers them.

A useful test is: **Can a maintainer make one clear accept / return decision from the evidence produced by this Issue?** If not, narrow or split it.

### 4. Write the Organization Work Item contract

Follow [`../../.github/ISSUE_TEMPLATE/work-item.yml`](../../.github/ISSUE_TEMPLATE/work-item.yml). Use:

- `Goal`
- `Context`
- `Scope`
- `Non-goals` when useful
- `Acceptance criteria`
- `Verification / evidence`
- `Dependencies / risks` when useful

Do not invent a competing Issue schema.

#### Goal

State one concrete outcome. Describe what becomes true when the work succeeds, not a vague activity such as "optimize", "improve", or "clean up" without a measurable boundary.

#### Context

Record only facts, constraints, prior decisions, links, and current-state evidence that materially affect implementation or acceptance.

Separate proven facts from assumptions. Verify current technical claims from repository/workflow/runtime state when practical.

#### Scope

Define the surfaces this work item owns. Keep scope narrow enough that unrelated cleanup is clearly excluded.

Do not prescribe implementation details unless they are themselves part of the accepted contract or safety boundary.

#### Non-goals

Use this section when explicit exclusions prevent predictable scope creep. Do not fill it with ceremonial negatives that add no boundary value.

#### Acceptance criteria

Write observable, checkable outcomes. Each criterion must be decidable from evidence.

Prefer statements such as:

- an exact contract or behavior exists;
- a specified failure path is handled;
- a repository/runtime boundary remains unchanged;
- a named validation succeeds;
- a required artifact or link exists.

Avoid criteria that only say code was written, a refactor was attempted, or something "looks better" without an acceptance method.

#### Verification / evidence

Describe the evidence required to prove the acceptance criteria. Match verification cost to the changed surface.

Use the Organization testing language in [`../../docs/engineering/testing-standard.md`](../../docs/engineering/testing-standard.md) when T1–T5 semantics apply, but do not require expensive builds or environment tests for unrelated surfaces.

At Issue creation time, describe **required future evidence**. Never write an unexecuted test, build, deployment, device check, or smoke as if it has already passed.

#### Dependencies / risks

Record only material blockers, ordering constraints, rollback concerns, external dependencies, or known uncertainty.

A dependency should not become an excuse to make one Issue own several independently verifiable tasks.

### 5. Keep metadata out of the Issue body

Do not duplicate GitHub-owned management metadata or relationships in prose. Examples include:

- Project `Status`;
- Priority / Effort / Start date / Target date;
- assignees;
- linked pull requests;
- milestones;
- sub-issue progress.

Ordinary creation relies on Organization intake to add the open Issue to `Mira Development`; current native Project behavior gives a newly added item `Status=Todo`.

Do not manually set a second lifecycle field or write "current status" into the Issue body to compensate for Project metadata.

The Issue contract must remain meaningful even if the management projection is temporarily stale.

### 6. Creation and execution authority are separate

Creating a work item **by itself** does not authorize implementation, branch creation, merge, deployment, release, acceptance, or other side effects.

However, do not manufacture an extra confirmation round when the current maintainer instruction already contains a separate, explicit authorization for the next action. For example, "开一张卡然后开始施工" contains both creation and execution authority; create the Issue first, then follow the lifecycle and repository contracts for the authorized work.

When implementation begins under explicit authority, Project `Status` should move to `In Progress` according to [`../../docs/governance/work-item-lifecycle.md`](../../docs/governance/work-item-lifecycle.md). If the current tool cannot mutate Project Status, do not create a shadow field; treat that as a management-projection gap rather than an engineering blocker.

This Skill must not be invoked by an independent AI reviewer to autonomously convert review findings into follow-up Issues. Review findings remain advisory until a maintainer explicitly decides to formalize work.

## Quality check before creation

Before submitting the Issue, confirm:

- the owning repository is correct;
- no existing Issue already owns the same outcome;
- there is one coherent acceptance decision;
- scope is small enough for a short implementation and verification loop;
- acceptance criteria are observable;
- required evidence is explicit and proportionate;
- current facts were not inferred from stale docs when better evidence exists;
- GitHub-owned metadata/relationships are not duplicated in prose;
- creation has not been mistaken for implementation authority;
- no unrelated implementation or cleanup has been smuggled into the work item.

If these checks fail, refine or split the work item before creating it.
