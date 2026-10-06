# External Worker evidence package

Status: active Organization guidance.

The Mira External Worker emits a bounded evidence package for every run that reaches the evidence finalizer. This package complements GitHub Actions logs; it does not replace the GitHub Issue, branch, commit, pull request, or Actions run as the durable engineering ledger.

## Package

The reusable Worker currently uploads:

- `worker-run.json` — run identity, base/branch identity, pinned OpenCode/model/Skill identity, trusted step outcomes, terminal status, failure stage, commit/PR pointers, trusted verification identity, retention, and safety metadata.
- `trajectory.jsonl` — metadata-only OpenCode session activity derived from a sanitized native session export. It records tool/step identity and state but omits prompt text, reasoning, tool arguments, and tool results.
- `session-summary.json` — whether a structured OpenCode export was available, resolved session ID, event count, event bound, and truncation state.
- `worker-output.txt` and `worker-output-meta.json` — bounded Worker handoff/output plus byte/truncation metadata.
- `verification.log` and `verification-meta.json` — bounded trusted verification output plus byte/truncation metadata.
- `changed-files.txt`, `committed-files.txt`, and `diff-stat.txt` — bounded repository mutation summaries without persisting a full repository snapshot.

Exact filenames are an implementation detail. The durable contract is that equivalent evidence remains machine-readable, bounded, attributable to one immutable run identity, and useful on both success and failure paths.

## Trust boundary

The evidence package distinguishes two classes of activity:

1. model-owned repository reasoning/edit activity, represented by the OpenCode session-derived metadata trajectory and bounded Worker output;
2. trusted workflow-owned validation, verification, Git mutation, and Draft PR stages, represented by explicit GitHub Actions step outcomes in `worker-run.json`.

A model session cannot grant itself merge, Issue outcome, release, deployment, promotion, or broader workflow authority.

## OpenCode integration

Use OpenCode's supported session/export surface rather than wrapping or reimplementing the agent loop.

The Worker:

1. snapshots visible session IDs before model execution;
2. runs the pinned OpenCode session;
3. resolves the newly created session when possible;
4. requests a sanitized native JSON export;
5. extracts only metadata needed for audit/recovery;
6. deletes the intermediate sanitized export before artifact upload.

If a sanitized structured export is unavailable, the package records that limitation explicitly instead of persisting an unsanitized transcript.

## Secret and size safety

Persisted evidence must not contain provider credentials, GitHub tokens, environment dumps, private reasoning text, raw prompt bodies, or unbounded tool inputs/results.

Current bounds:

- Worker persisted output: 120 KB maximum.
- Trusted verification persisted output: 120 KB maximum.
- Session-derived trajectory: 500 events maximum.
- Actions artifact retention: 14 days.

Truncation is explicit in companion metadata rather than silently dropping content.

## Failure semantics

`worker-run.json` records every trusted stage outcome and derives:

- `terminal_status`;
- `failure_stage`;
- the last stages that completed successfully;
- commit and Draft PR pointers only when those states were actually reached.

A run that fails before commit or PR creation must still be diagnosable from the package without prior ChatGPT-thread memory.

## Source of truth

Evidence is diagnostic and audit material.

- the GitHub Issue owns the work-item contract and outcome;
- repository/workflow/runtime state owns current technical reality;
- the Actions run owns execution-state evidence;
- branch/commit/PR state owns Git delivery evidence;
- this package provides a bounded reconstruction aid for one Worker run.

Do not turn the package into a second task ledger, monitoring database, retry controller, or permanent transcript store.
