# Repository Migration SOP

This SOP is based on the first completed Mira Organization migration pilot: `uichat-mira/uichat-mira-relay`.

The goal is not merely to move a repository between owners. A migration is complete only when ownership, CI/CD, environment semantics, and production verification have been checked.

## Principle

Migrate one repository at a time.

Do not bundle unrelated refactors, cleanup, branch deletion, or product changes into the migration unless they are required to make the migration safe.

## Phase 1 — Preflight audit

Before transfer, inspect the current repository as it actually exists.

Minimum audit:

- default branch;
- all active branches and their real responsibilities;
- branch protection, rulesets, and branch policies;
- GitHub Actions workflows and recent runs;
- releases and tags;
- GitHub Environments;
- repository secrets and variables;
- webhooks;
- installed GitHub Apps and integrations;
- deployment configuration;
- external runtime resources;
- hard-coded references to the old owner/repository path.

For Cloudflare-backed repositories, also identify which capabilities are actually used, for example Workers, Pages, R2, D1, Durable Objects, Workers AI, Workflows, DNS, or custom domains.

Do not infer usage from naming alone. Verify configuration and workflow files.

## Phase 2 — Repository transfer

Transfer the repository to the `uichat-mira` Organization.

Do not delete branches or rewrite history during transfer.

### Checkpoint 1 — Repo Transfer Accepted

Verify after transfer:

- repository identity is preserved rather than copied;
- expected branches are present;
- default branch did not change unexpectedly;
- Actions history is preserved;
- releases/tags are preserved where applicable;
- old GitHub URL redirects to the new repository;
- workflows and deployment configuration are still present;
- no new hard-coded dependency on the old owner was introduced.

Only after this checkpoint passes should migration continue.

## Phase 3 — Organization credentials

Prefer organization-level CI/CD credentials for shared infrastructure when the same credential is intentionally used across Mira repositories.

Current shared Cloudflare GitHub Actions names:

```text
CLOUDFLARE_API_TOKEN
CLOUDFLARE_ACCOUNT_ID
```

Rules:

- never commit credential values;
- do not copy secret values into documentation;
- do not delete a repository-level credential until the organization-level replacement has been verified in a real workflow run;
- remember that GitHub Actions secrets and runtime application secrets are different things.

A Cloudflare control-plane token can authorize deployment, but it does not replace third-party runtime secret values such as provider API keys or GitHub destination tokens.

## Phase 4 — Environment alignment

Align deployment semantics with the Mira environment model:

```text
feat/* → dev → test → prod
```

Expected deployment behavior:

- `feat/*`: CI only;
- `dev`: development deployment;
- `test`: test/acceptance deployment;
- `prod`: production deployment.

Historical `main` may remain, but it must not bypass `prod` and deploy production.

Where possible, use separate runtime resources for `dev`, `test`, and `prod`.

## Phase 5 — Progressive deployment verification

Do not jump directly from migration to production.

Promote the same validated change progressively:

1. deploy `dev`;
2. verify CI and deployment;
3. promote to `test`;
4. verify CI and deployment;
5. promote to `prod`;
6. verify production health or smoke behavior.

If a lower environment fails, stop promotion and diagnose before continuing.

## Checkpoint 2 — Organization CI/CD Accepted

A runtime repository passes this checkpoint when:

- organization credentials are read successfully;
- CI passes;
- `dev` deployment passes when applicable;
- `test` deployment passes when applicable;
- `prod` deployment passes;
- production health/smoke verification passes;
- production can be deployed without relying on a developer's local machine.

## Relay pilot record

The Relay pilot established the current baseline:

```text
feat/* → CI only
dev    → uichat-mira-relay-dev
test   → uichat-mira-relay-test
prod   → uichat-mira-relay + relay.tomz.io
main   → no deployment
```

The pilot passed both repository-transfer and organization-CI/CD checkpoints.

Future migrations should reuse this sequence, adapting only the repository-specific runtime and acceptance checks.
