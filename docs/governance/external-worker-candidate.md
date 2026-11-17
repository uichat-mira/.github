# External Worker Candidate Contract

Status: active implementation contract. AGT-056 established the primitive, AGT-057 made Candidate durable on controllable failure paths, AGT-058 separates clean-room Verify from least-privilege Delivery, and AGT-059 adds cross-run Recovery.

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
| `contract_fingerprint` | Lowercase `sha256:<64 hex>` value produced by the AGT-059 deterministic execution-aware fingerprint over the Issue/amendments, explicit base branch, and verification-command hash. |
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

## Production Worker integration

The canonical reusable External Worker is split into three real GitHub Actions jobs with separate runners and permission scopes:

1. **Worker/Capture**
   - runs the model and edits the ephemeral workspace;
   - freezes and uploads the Candidate before trusted verification;
   - has `contents: read`, `issues: read`, and no pull-request write permission;
   - is the only job that may receive provider credentials.
2. **Verify**
   - starts on a fresh GitHub-hosted runner;
   - checks out the exact Candidate `base_sha`;
   - downloads the immutable Candidate Artifact;
   - restores it with the pinned AGT-056 Candidate primitive and verifies patch digest / reconstructed tree identity;
   - runs the caller-owned verification command only after restore succeeds;
   - has only `contents: read`; same-run Candidate Artifact transfer uses the Actions artifact runtime without granting REST `actions` permission, and no provider credential is present.
3. **Delivery**
   - starts on another fresh runner only after Verify succeeds;
   - checks out the same exact `base_sha`, downloads the same Candidate and Verify evidence, restores again, and mechanically rechecks patch/tree identity;
   - commits only the restored verified tree;
   - asserts the resulting commit tree equals the verified Candidate tree;
   - is the only job with `contents: write` and `pull-requests: write`; it has no Issue permission and uses those writes solely for pushing the isolated Worker branch and opening the Draft PR.

The Candidate implementation is still pinned to immutable AGT-056 commit `c5d93e149765f9068f3d342d2aed3a40a8f20efc`. A successful Verify or Delivery restore means the exact frozen code state was reproduced; it never grants merge, Issue outcome, release, deployment, or promotion authority.

The current Candidate Artifact retention remains 14 days. This is a bounded recovery window, not permanent storage.

AGT-059 replaces the transitional fingerprint with the deterministic execution-aware Recovery contract described in [`external-worker-recovery.md`](external-worker-recovery.md). Candidate reuse requires both the canonical fingerprint and ambiguity guard to match; changing the target base branch or caller verification command prevents silent reuse.

### Failure semantics after AGT-058

- Worker/provider failure after edits can still leave a recoverable Candidate Artifact.
- Candidate capture/upload failure remains non-recoverable and explicit.
- Verify restore/digest/tree failure stops before Delivery and therefore produces no Git push or Draft PR.
- Repository verification failure leaves the Candidate and Verify evidence intact and produces no Delivery.
- Delivery failure occurs after a verified Candidate exists; AGT-059 records it as `delivery_retry_only`, validates the prior Delivery evidence, and retries idempotently on the Candidate-origin branch without re-running the model.
- Hard runner loss, force cancellation, platform termination, and hostile same-runner compromise remain outside the guarantee.

The reusable workflow's `timeout_minutes` input is retained for caller compatibility but is now an advisory planning budget, defaulting to 60 minutes. It is not wired to a job/step timeout and must not kill a Worker when the budget elapses. GitHub-hosted runner platform limits remain an external ceiling; the workflow does not claim protection from platform termination.

### Caller compatibility and rollout boundary

The reusable workflow input/output contract remains compatible: existing callers still pass `issue_number`, `base_branch`, `verification_command`, timeout, provider/model routing and provider secrets, and still receive Worker branch / Draft PR outputs.

Mira product repositories currently pin immutable historical workflow SHAs. Merging AGT-059 into `uichat-mira/.github@main` therefore does **not** silently switch Desktop, Mobile, Relay, or other callers to the Recovery-enabled engine. Each caller must deliberately repin to an accepted AGT-058 engine SHA.

The Organization free-worker wrapper also remains pinned to its existing historical engine until an explicit reviewed repin. AGT-059 additionally requires future callers to grant `actions: read` for prior-run Artifact recovery and `issues: write` for the isolated Recovery pointer job. These permissions are not silently introduced into existing pinned callers.
