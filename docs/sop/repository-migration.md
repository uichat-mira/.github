# Migration SOP v1

Use this SOP for Mira repository migrations into the `uichat-mira` Organization.

The rule is simple: **move one repository at a time, verify reality at every checkpoint, and keep a rollback anchor before production changes.**

## Flow

```text
Preflight audit
→ Transfer
→ Branch / CI organization
→ Secrets / App authorization
→ Prod deploy
→ Health / smoke
→ Close with rollback anchor
```

## 1. Preflight audit

Before transfer, record the current real state:

- default branch and active branches;
- branch protection / rulesets;
- Actions workflows and recent runs;
- releases / tags / environments;
- repository secrets / variables;
- required GitHub Apps / integrations;
- deployment config and external runtime resources;
- hard-coded old owner/repository references.

Do not infer. Read the repository and current runtime state.

## 2. Transfer

Transfer the repository to `uichat-mira`.

Immediately verify:

- repository identity/history is preserved;
- expected branches, Actions history, releases and tags remain;
- old repository URL redirects;
- workflow/config files survived unchanged unless intentionally modified.

This is **Checkpoint 1: Repo Transfer Accepted**.

## 3. Branch / CI organization

Align deployment semantics to:

```text
feat/* → dev → test → prod
```

- `feat/*`: CI only
- `dev`: development integration/deploy
- `test`: test/acceptance deploy
- `prod`: production deploy
- historical `main`: may remain, but must not bypass `prod`

Promote the same validated change through environments where practical.

## 4. Secrets / App authorization

Verify the transferred repository can actually use every required organization credential and integration.

For shared Cloudflare CI/CD, current organization secrets are:

```text
CLOUDFLARE_API_TOKEN
CLOUDFLARE_ACCOUNT_ID
```

Also verify any required GitHub App / installation authorization after transfer.

Do not remove old repository-level credentials until the organization-level replacement has succeeded in a real workflow run.

## 5. Prod deploy

Only after lower-environment verification, deploy from `prod`.

Production must be deployable from CI/CD without depending on a developer's local machine.

## 6. Health / smoke

After production deployment, run the smallest meaningful production verification:

- health endpoint;
- smoke request;
- artifact availability;
- or another repository-specific acceptance check.

A successful deploy command alone is not enough.

## 7. Rollback anchor

Before declaring migration complete, record enough information to restore the last known-good production state.

Minimum:

- last known-good source commit/tag;
- last known-good deployed version/release identifier;
- rollback mechanism or command if the platform requires one.

This is **Checkpoint 2: Organization CI/CD Accepted**.

## Relay pilot

`uichat-mira/uichat-mira-relay` is the reference implementation for v1.

Verified flow:

```text
feat/* → CI only
dev    → uichat-mira-relay-dev
test   → uichat-mira-relay-test
prod   → uichat-mira-relay + relay.tomz.io
main   → no deployment
```

Verified production:

- new production version: `9682efd1-cb72-4ec6-8a84-cfa9273bbba2`
- health: `ok=true`, service `mira-remote-relay`, protocolVersion `1`
- previous production Worker version / rollback anchor: `bb534ec3-61a5-47b9-9a50-d71f47c4c336`
- pre-environment-alignment source anchor: `cc0dc57d4772f31f73e4e853b20275c7c1843a5e`

Relay passed both checkpoints.

## Done means done

A repository migration is complete only when:

```text
transfer verified
+ CI organization verified
+ required secrets/apps verified
+ prod deployed by CI
+ production health/smoke passed
+ rollback anchor recorded
```
