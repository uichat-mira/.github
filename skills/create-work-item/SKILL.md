---
name: create-work-item
description: Create small, independently verifiable Mira Organization engineering work items as GitHub Issues while preserving the Organization source-of-truth model.
---

# Create Work Item

Use this Skill when a maintainer asks to create, split, formalize, or record an engineering task for a repository under `uichat-mira`.

The output of this Skill is a **GitHub Issue work-item contract**. It is not a second ledger, an implementation plan pretending to be a contract, or a Project status update.

## Core principles

Every work item must satisfy both rules:

1. **Independently verifiable** — there must be concrete evidence that can decide whether this work item is accepted.
2. **Small and fast** — prefer the smallest coherent change that can be implemented, reviewed, verified, and reverted without dragging unrelated work with it.

Small does not mean artificially fragmented. Keep changes together when they form one atomic behavior and cannot be meaningfully accepted separately.

## Sources of truth

Before creating a work item, respect the Organization truth model in [`../../docs/governance/source-of-truth.md`](../../docs/governance/source-of-truth.md):

- repository / workflow / runtime state is authoritative for current technical reality;
- GitHub Issue is the engineering source of truth for a work item;
- Organization and repository docs define policy and procedure;
- GitHub Project is a management projection;
- public website content is a public projection.

Do not make an outdated document override observable code, configuration, workflow, or runtime state.

When the maintainer has made a newer explicit decision that conflicts with existing written guidance, do not silently choose one side or rewrite the older guidance as part of this task. Surface the conflict and resolve the intended contract first.

## Procedure

### 1. Identify the owning repository

Determine which repository owns the behavior, contract, runtime, documentation, or infrastructure being changed.

Use current repository reality rather than naming guesses. If repository-local collaboration guidance exists, read the relevant current files such as root `AGENTS.md`, repository policy/docs, active contract documents, and branch rules when they materially affect scope or verification.

For work spanning repositories, prefer separate work items when each repository has an independently implementable and verifiable outcome. Cross-link them and identify the contract owner where relevant.

Do not create multiple repository Issues merely because several repositories are mentioned. Split only when there are distinct acceptance decisions.

### 2. Check for existing work

Before creating a new Issue, search the owning repository and, when useful, the Organization for:

- the same outcome;
- the same defect or symptom;
- the same contract change;
- an active parent or child work item that already owns the scope.

If an existing Issue already owns the outcome, prefer using or updating that work item instead of creating a duplicate. If the new work is distinct but related, link the relationship explicitly.

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

Follow the existing Organization Issue contract in [`../../.github/ISSUE_TEMPLATE/work-item.yml`](../../.github/ISSUE_TEMPLATE/work-item.yml). Use these sections:

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

### 5. Leave management projection to Project automation

Do not duplicate Project-owned management metadata in the Issue body, including fields such as:

- Stage;
- Target date;
- Effort;
- Assignees;
- Linked pull requests;
- Sub-issues progress.

Do not manually add the Issue to `Mira Development` or set an initial Stage as part of ordinary work-item creation. Existing Organization automation owns Project intake and defaults an empty Stage to `Backlog`.

The Issue contract must remain meaningful even when the Project projection is stale or temporarily unavailable.

### 6. Stop after creating the work item

Creating a work item does not implicitly authorize implementation, branch creation, merge, deployment, release, acceptance, or Project status mutation.

Those actions follow their own repository and Organization contracts.

This Skill must not be invoked by an independent AI reviewer to autonomously turn review findings into follow-up Issues. Review findings remain advisory until a maintainer explicitly decides to create or formalize work.

## Quality check before creation

Before submitting the Issue, confirm:

- the owning repository is correct;
- no existing Issue already owns the same outcome;
- there is one coherent acceptance decision;
- scope is small enough for a short implementation and verification loop;
- acceptance criteria are observable;
- verification evidence is explicit and proportionate;
- current facts were not inferred from stale docs when better evidence exists;
- Project management fields are not duplicated in prose;
- no unrelated implementation or cleanup has been smuggled into the work item.

If these checks fail, refine or split the work item before creating it.
