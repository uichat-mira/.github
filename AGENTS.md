# Mira Organization AI Instructions

Policy revision: `2026-09-11.1`

This file is the canonical AI collaboration entry for repositories owned by the `uichat-mira` GitHub Organization.

Use it as an **Organization-level router and standing contract**, not as a replacement for repository-specific instructions or the underlying policy documents it references.

## Start here

When working on a `uichat-mira` repository:

1. Use the current retrieved version of this file. Do not substitute a remembered or previously cached copy when the current source is available.
2. Read the target repository's root `AGENTS.md` and any more specific instructions that apply to the files or task in scope.
3. Read the current Issue / PR / task contract for the work being performed.
4. Load only the Organization policy, SOP, or Skill relevant to the current task.
5. Verify technical claims against the actual repository, workflow, configuration, or runtime when practical.

If the current Organization instructions cannot be retrieved, say so explicitly. Do not invent, reconstruct, or silently rely on remembered Organization rules.

## Two kinds of precedence

Do not confuse **instruction priority** with **factual truth**.

### Instruction priority

For what the AI should do on a specific task, use this order:

1. current explicit maintainer/user instruction for the task;
2. current Issue / PR / task contract;
3. applicable repository-specific `AGENTS.md`, policy, or documented exception;
4. applicable Organization policy, SOP, or Skill from this repository;
5. generic engineering practice or model defaults.

A higher-priority instruction can change the requested outcome, but it does not make an unverified technical claim true.

If two applicable instructions materially conflict and the intended contract is not clear, surface the conflict before proceeding. Do not silently choose a convenient interpretation.

### Factual truth

For what currently exists or runs, follow [`docs/governance/source-of-truth.md`](docs/governance/source-of-truth.md). In short:

1. actual code / configuration / workflow / runtime for current technical reality;
2. GitHub Issue for the agreed state of a specific work item;
3. Organization and repository docs for policy and procedure;
4. GitHub Project for management presentation;
5. `mira.tomz.io` for public presentation.

Repair stale projections instead of forcing observable reality to match them.

## Organization routing

Load only what the current task needs.

| Task | Read |
| --- | --- |
| Create, split, formalize, or record an engineering work item | [`skills/create-work-item/SKILL.md`](skills/create-work-item/SKILL.md) |
| Determine work-item / Project / policy source-of-truth boundaries | [`docs/governance/source-of-truth.md`](docs/governance/source-of-truth.md) |
| Apply shared test layers, evidence, or promotion verification | [`docs/engineering/testing-standard.md`](docs/engineering/testing-standard.md) |
| Reason about `feat/* → dev → test → prod` environment semantics | [`docs/engineering/environment-model.md`](docs/engineering/environment-model.md) |
| Perform Organization AI PR Review | [`ai-review/POLICY.md`](ai-review/POLICY.md) and [`ai-review/OUTPUT-CONTRACT.md`](ai-review/OUTPUT-CONTRACT.md) |
| Migrate a repository into the Organization | [`docs/sop/repository-migration.md`](docs/sop/repository-migration.md) |

Do not preload every Skill or policy merely because the repository belongs to Mira. Use progressive disclosure.

## Work-item discipline

Organization engineering work should be small enough to verify in a short loop and have concrete acceptance evidence.

When creating or splitting work, do not improvise the detailed contract from this paragraph. Read and follow [`skills/create-work-item/SKILL.md`](skills/create-work-item/SKILL.md).

GitHub Issue is the work-item truth. GitHub Project is its management projection. Do not duplicate Project-owned management state into Issue prose unless a specific contract requires it.

## Repository ownership

Organization-wide rules, reusable SOPs, and Organization Skills belong in `uichat-mira/.github`.

Repository-specific architecture, implementation constraints, build commands, product boundaries, and documented exceptions belong in the repository that owns them.

Do not copy Organization policy into a repository merely for convenience. Reference the canonical source unless an offline or runtime-specific requirement explicitly justifies a managed copy.

## Stop conditions

Stop and report the gap instead of guessing when:

- current Organization guidance is required but cannot be retrieved;
- the target repository or owning surface is ambiguous;
- an applicable repository contract materially conflicts with an Organization contract and precedence does not resolve the intended action;
- required evidence is unavailable but would be necessary to claim completion or safety.

Never report an unexecuted test, build, deployment, review, or smoke check as passed.
