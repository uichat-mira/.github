# Mira Organization

This repository contains organization-wide engineering policy, reusable SOPs, GitHub defaults, and collaboration Skills for the `uichat-mira` Organization.

## AI Instructions

- [Organization AGENTS.md](AGENTS.md) — canonical Organization-level AI instruction entry and progressive-disclosure router for policies, SOPs, and Skills

## Engineering

- [Environment Model](docs/engineering/environment-model.md) — `feat/* → dev → test → prod`
- [External Worker Lifecycle](docs/engineering/external-worker-lifecycle.md) — current Worker/Candidate/Verify/Delivery/Recovery/Reporter lifecycle and role-boundary entry
- [Mira Cloud Core Specification](docs/engineering/mira-cloud.md) — shared backend naming, service boundaries, client contracts, and unified authentication semantics
- [Mira Cloud MCP Inter-service Collaboration](docs/engineering/mira-cloud-mcp.md) — lightweight optional MCP collaboration, service identity, delegated authorization, tool contracts, and validation (proposal)
- [号脉 (How Am I) / Reporter / Worker Workforce V1 Contract](docs/engineering/how-am-i-reporter-workforce-v1.md) — worker-only, zero-new-cost observability and GitHub-owned workforce control
- [Organization Testing Standard](docs/engineering/testing-standard.md) — shared test layers, command semantics, CI evidence, and promotion gates

## SOP

- [Repository Migration SOP](docs/sop/repository-migration.md) — audit, transfer, organization CI/CD, progressive deployment, and acceptance checkpoints

## Governance

- [Source of Truth](docs/governance/source-of-truth.md) — responsibilities of Issues, Projects, organization docs, runtime state, and mira.tomz.io
- [External Worker Provider and Model](docs/governance/external-worker-provider-model.md) — run-scoped provider/profile/model selection for the reusable External Worker
- [External Worker Evidence Package](docs/governance/external-worker-evidence.md) — bounded evidence package emitted by the reusable External Worker
- [External Worker Candidate Recovery](docs/governance/external-worker-recovery.md) — cross-run Candidate discovery, contract fingerprinting, fail-closed continuation, and Delivery-only retry

## Collaboration Skills

- [Create Work Item](skills/create-work-item/SKILL.md) — create small, independently verifiable GitHub Issue work items without duplicating Project management state

## Scope

Keep organization-wide rules and collaboration Skills here.

Repository-specific implementation details belong in the repository that owns them. If a repository needs to diverge from an organization rule, document the exception locally rather than silently redefining the organization convention.
