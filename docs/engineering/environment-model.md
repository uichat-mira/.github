# Environment Model

This document defines the organization-wide branch-to-environment convention for Mira repositories.

## Standard flow

```text
feat/* → dev → test → prod
```

### feat/*

Purpose: isolated feature or fix work.

Expected behavior:

- CI only.
- Must not deploy to a shared runtime environment.
- Normally merges into `dev`.

### dev

Purpose: development integration environment.

Expected behavior:

- Receives completed feature work.
- Runs CI.
- May deploy to a dedicated development environment.
- Used to verify integration before promotion.

### test

Purpose: test and acceptance environment.

Expected behavior:

- Receives code promoted from `dev`.
- Runs CI.
- Deploys to a dedicated test environment when the repository has a runtime.
- Used for regression, smoke, and acceptance checks before production.

### prod

Purpose: production source branch.

Expected behavior:

- Receives code promoted from `test`.
- Runs CI.
- Is the only environment branch allowed to deploy production.
- Production health or smoke verification should run after deployment where practical.

## About main

`main` is not part of the Mira environment model.

A repository may retain `main` for historical compatibility, migration safety, or external tooling. If retained:

- `main` must not implicitly mean production.
- `main` must not bypass `prod` and deploy production.
- Deleting or renaming `main` is a separate repository-governance decision and is not required merely to adopt this environment model.

## Default branch

GitHub's default branch is a workflow/UI choice, not an environment definition.

Changing the default branch does not change which branch is production. Each repository may choose its default branch based on its working model, while deployment semantics remain governed by this document.

## Promotion principle

Promotion should move an already-reviewed commit through environments rather than rebuild unrelated changes at every stage:

```text
feat/* → dev → test → prod
```

For high-risk repositories, promotion may require explicit approval or additional checks, but it must not skip environment semantics without a documented exception.

## Exceptions

If a repository cannot reasonably implement all four stages, document the exception in that repository.

An exception must state:

- which stage is omitted;
- why it is omitted;
- what check replaces it;
- how production remains protected.
