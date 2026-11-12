# External Worker Candidate Contract

Status: active implementation contract for AGT-056. Production Worker integration is not part of this change.

A Candidate is the durable, recoverable code state produced by one External Worker attempt before trusted verification and GitHub delivery. It is **not** a pull request, acceptance decision, verification result, or second task ledger.

## Candidate identity

A Candidate consists of exactly two core files:

- `candidate.patch` — a binary/full-index Git patch from one immutable base commit to the Worker workspace snapshot;
- `candidate.json` — a versioned manifest that binds that patch to repository, Issue, run, base, contract fingerprint, digest, and reconstructed Git tree identity.

Diagnostic evidence such as `worker-run.json`, trajectories, model output, verification logs, changed-file summaries, and later Reporter projections may travel beside a Candidate, but they are not part of Candidate identity.

## Manifest schema v1

`candidate.json` uses `schema_version: 1` and contains:

| Field | Contract |
| --- | --- |
| `repository` | GitHub repository in `owner/name` form. |
| `issue_number` | Positive GitHub Issue number that owns the work contract. |
| `run_id` / `run_attempt` | Execution identity for the Worker attempt. |
| `base_branch` | Explicit delivery-base branch name captured as provenance. |
| `base_sha` | Exact Git commit used to construct the Candidate. Restore must run at this exact commit. |
| `contract_fingerprint` | Lowercase `sha256:<64 hex>` value. AGT-056 validates its format; canonical Issue/amendment fingerprinting belongs to later Recovery work. |
| `candidate_patch_sha256` | Lowercase SHA-256 digest of `candidate.patch`, prefixed with `sha256:`. |
| `candidate_patch_bytes` | Exact patch byte length. |
| `candidate_tree_oid` | Git tree OID produced from the frozen Candidate index. |
| `provider` / `model` | Optional execution provenance only; not part of correctness or acceptance. |
| `worker_outcome` | Lowercase stable outcome token describing the Worker attempt. A failed Worker may still produce a valid Candidate. |
| `created_at` | UTC creation time or trusted caller-supplied equivalent. |
| `changed_paths` | Candidate path summary derived from the frozen index. It is convenience metadata, not identity. |
| `safety` | Bounded implementation metadata describing capture safety checks and unsupported surfaces. |

The three code-state anchors are:

1. `base_sha` — where construction started;
2. `candidate_patch_sha256` — whether the Candidate payload changed;
3. `candidate_tree_oid` — whether a clean restore reconstructs the exact frozen Git tree.

Restore fails closed when any of those identities disagree.

## Capture contract

The trusted capture tool is `.github/scripts/worker-candidate/candidate.py capture`.

Capture:

1. resolves the trusted base to an exact commit;
2. creates a **temporary Git index** initialized from that base;
3. stages the complete workspace snapshot into the temporary index with `git add -A`;
4. leaves the caller's real Git index untouched;
5. rejects changed gitlinks/submodules because AGT-056 does not prove their round-trip behavior;
6. applies explicit sensitive-path and secret-like-content heuristics;
7. writes a bounded `--binary --full-index --find-renames` patch;
8. records patch SHA-256 and `git write-tree` identity;
9. writes schema-v1 `candidate.json`.

Capture does not commit, push, create a branch, create a PR, mutate an Issue, call a model, or persist an environment dump.

The default patch-size ceiling is 10 MiB. A trusted caller may choose another explicit bound. Exceeding the bound rejects the Candidate rather than silently truncating it.

## Restore contract

The trusted restore tool is `.github/scripts/worker-candidate/candidate.py restore`.

Restore requires caller-supplied expected repository, Issue and base identity. It then:

1. requires a clean Git worktree;
2. verifies schema version and required manifest fields;
3. verifies repository / Issue / trusted expected base identity;
4. requires `HEAD` to equal the exact Candidate base commit;
5. verifies optional trusted contract fingerprint when supplied;
6. verifies patch SHA-256 and exact byte length before applying code;
7. applies the patch to the Git index/worktree;
8. recomputes `git write-tree`;
9. requires the restored tree OID to equal `candidate_tree_oid`.

A successful restore means the code state is reproduced. It does **not** mean the code is correct, verified, accepted, safe to merge, or ready to deploy.

## Proven AGT-056 round-trip surface

The repository fixture proves Candidate round-trip behavior on the GitHub-hosted Ubuntu/Git implementation for:

- tracked file modification;
- untracked file addition;
- deletion;
- rename;
- binary content;
- executable-bit change;
- symlink addition;
- empty change.

The fixture also proves fail-closed behavior for:

- patch digest mismatch;
- wrong restore base;
- reconstructed tree mismatch;
- obvious sensitive path;
- obvious secret-like content;
- Candidate exceeding the configured size ceiling.

Changed submodule/gitlink state is intentionally rejected in schema-v1 capture because this card does not prove safe restoration for it.

## Safety boundary

Candidate Artifacts are materially more sensitive than current `diff-stat` or changed-file evidence because they persist source content.

Schema-v1 therefore includes bounded fail-closed checks for obvious cases such as:

- `.env`, local credential files, private-key file extensions and similar sensitive paths;
- recognizable private-key blocks and selected well-known credential prefixes;
- oversized patches.

These checks reduce risk; they are **not** a complete secret scanner and must never be described as one. Later production integration may add stronger repository-specific or Organization-wide scanning, but it must not weaken the digest/tree identity contract.

## Source-of-truth boundary

- GitHub Issue owns the work contract and outcome.
- Candidate owns one recoverable code-state snapshot for one run.
- Trusted verification owns test/validation evidence against that Candidate.
- Branch/commit/PR owns Git delivery evidence.

A Candidate may exist when the Worker failed, was blocked, or has not been independently verified. Saving it preserves work; it does not grant authority.
