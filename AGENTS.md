# Mira Organization AI Instructions

Policy revision: `2026-09-11.2`
Constitution: `v1`

This file is the canonical AI collaboration entry for repositories owned by the `uichat-mira` GitHub Organization.

It contains the durable Organization constitution plus routing to task-specific policy, SOP, and Skills. It must stay concise: detailed domain rules belong in their owning documents, not duplicated here.

## Constitution v1

### 1. Small and independently verifiable

Prefer the smallest coherent unit of work that can be implemented, reviewed, verified, and reverted without dragging unrelated work with it.

A task is not complete because code changed. It is complete only when the agreed outcome can be decided from concrete evidence.

### 2. One concern, one source of truth

Do not maintain the same decision independently in several places.

- code / configuration / workflow / runtime describe current technical reality;
- GitHub Issue owns the work-item contract;
- GitHub Project is a management projection;
- Organization docs own Organization policy and reusable SOPs;
- repository docs own repository-specific rules and exceptions.

When projections disagree, repair the stale projection instead of creating another copy.

### 3. Verify reality before inference

When current technical state matters, inspect the actual repository, workflow, configuration, or runtime when practical.

Do not let remembered behavior, stale documentation, naming guesses, or generic model knowledge override observable reality.

### 4. Authority is explicit

A role may act only within the authority granted by the current task and its applicable contract.

Creating a work item does not authorize implementation. Reviewing does not authorize editing, merging, acceptance, release, or Project-state mutation unless a separate contract explicitly grants that authority.

### 5. Conflicts are surfaced, not silently reconciled

If current instructions, repository contracts, Organization policy, or observable reality materially disagree, identify the conflict and resolve the intended contract before proceeding when precedence does not already decide it.

Do not invent a convenient interpretation merely to keep moving.

### 6. Completion requires evidence

Never report an unexecuted test, build, deployment, review, device check, or smoke check as passed.

If required evidence is unavailable, record the validation gap explicitly. Match verification cost to the changed surface; do not require expensive unrelated checks merely for ceremony.

### 7. Rules live with their owner

Organization-wide rules, reusable SOPs, and Organization Skills belong in `uichat-mira/.github`.

Repository-specific architecture, implementation constraints, build commands, product boundaries, and documented exceptions belong in the repository that owns them.

Do not copy Organization policy into repositories merely for convenience unless an offline or runtime-specific requirement justifies a managed copy.

### 8. Policy is versioned and current

Use the current retrieved version of this file when it is available. Do not substitute a remembered or previously cached copy.

`Policy revision` is the canary for remote retrieval. A task should be able to identify which current Organization policy it relied on when that matters for audit or verification.

## Start here

When working on a `uichat-mira` repository:

1. Retrieve the current version of this file.
2. Read the target repository's root `AGENTS.md` and any more specific instructions that apply to the task or files in scope.
3. Read the current Issue / PR / task contract for the work being performed.
4. Load only the Organization policy, SOP, or Skill relevant to the current task.
5. Verify current technical claims against repository/workflow/configuration/runtime evidence when practical.

If current Organization instructions cannot be retrieved, say so explicitly. Do not invent, reconstruct, or silently rely on remembered Organization rules.

## Instruction priority

For what the AI should do on a specific task, use this order:

1. current explicit maintainer/user instruction for the task;
2. current Issue / PR / task contract;
3. applicable repository-specific `AGENTS.md`, policy, or documented exception;
4. applicable Organization policy, SOP, or Skill from this repository;
5. generic engineering practice or model defaults.

A higher-priority instruction can change the requested outcome, but it does not make an unverified technical claim true.

## Factual truth

For what currently exists or runs, follow [`docs/governance/source-of-truth.md`](docs/governance/source-of-truth.md). In short:

1. actual code / configuration / workflow / runtime for current technical reality;
2. GitHub Issue for the agreed state of a specific work item;
3. Organization and repository docs for policy and procedure;
4. GitHub Project for management presentation;
5. `mira.tomz.io` for public presentation.

Do not confuse instruction priority with factual truth.

## Organization routing

Load only what the current task needs. Do not preload every Skill or policy merely because the repository belongs to Mira.

| Task | Read |
| --- | --- |
| Create, split, formalize, or record an engineering work item | [`skills/create-work-item/SKILL.md`](skills/create-work-item/SKILL.md) |
| Determine work-item / Project / policy source-of-truth boundaries | [`docs/governance/source-of-truth.md`](docs/governance/source-of-truth.md) |
| Apply shared test layers, evidence, or promotion verification | [`docs/engineering/testing-standard.md`](docs/engineering/testing-standard.md) |
| Reason about `feat/* → dev → test → prod` environment semantics | [`docs/engineering/environment-model.md`](docs/engineering/environment-model.md) |
| Perform Organization AI PR Review | [`ai-review/POLICY.md`](ai-review/POLICY.md) and [`ai-review/OUTPUT-CONTRACT.md`](ai-review/OUTPUT-CONTRACT.md) |
| Migrate a repository into the Organization | [`docs/sop/repository-migration.md`](docs/sop/repository-migration.md) |

## Stop conditions

Stop and report the gap instead of guessing when:

- current Organization guidance is required but cannot be retrieved;
- the target repository or owning surface is ambiguous;
- an applicable repository contract materially conflicts with an Organization contract and precedence does not resolve the intended action;
- required evidence is unavailable but would be necessary to claim completion, acceptance, or safety.
