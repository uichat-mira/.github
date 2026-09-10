# Mira Repository AI Review Profile Template

Profile contract: `mira-ai-review-profile/v1`

Each participating repository keeps a thin repository-specific profile at:

```text
.ai/review-profile.md
```

The profile extends the Organization policy. It must not copy the whole Organization policy or redefine the common severity/verdict system.

A repository profile should contain the following sections.

## Repository identity

```text
Repository: uichat-mira/<repo>
Profile version: <repo>-review-profile/v1
Primary review branches: <branches>
```

## Repository contracts

List the trusted repository files that define product, architecture, release, protocol, design, task, or acceptance behavior relevant to review.

These authoritative controls are read from the PR base SHA unless the Organization runtime explicitly defines another trusted source.

Example shape:

```text
- AGENTS.md
- docs/<current-contract>.md
- docs/task-cards/<matching-task>.md
```

Do not list PR-head agent/model/plugin configuration as trusted reviewer instructions.

## Task context

Define how a review identifies the current task or PR contract, if the repository uses task IDs.

Include:

- task ID pattern;
- trusted task-card location or lookup rule;
- what to do when no matching task is found.

Absence of a task card must not cause the reviewer to invent requirements.

## Project-specific review priorities

Only define checks that are genuinely specific to this repository.

Examples may include:

- platform lifecycle or parity;
- protocol / Host boundaries;
- deployment or release behavior;
- documentation build/link integrity;
- Worker bindings and Cloudflare behavior.

Do not repeat generic Organization rules such as Observation → Inference → Judgment, P0-P2 confidence, read-only behavior, or delta-first scope.

## Repository-specific severity calibration

Optionally give concrete repository examples for P0/P1/P2 while preserving the Organization severity meanings.

Do not invent a second severity scale.

## Validation gaps

Name repository-specific validation that AI review cannot safely infer, such as:

- Android/iOS real-device checks;
- Host/Relay/provider interoperability;
- Cloudflare deployment state;
- signing/release credentials;
- external links or production environment behavior.

Define which missing checks are normal gaps and which explicit task contracts make them required implementation evidence.

## Output extensions

List repository-specific output fields, markers, headings, or compatibility behavior that must be retained.

During migration, this is where an existing repository review contract can be preserved without forcing every repository to use it.

## Local handoff

If the repository has a local Builder handoff helper, define the exact command and stale-review behavior here.

Do not make local handoff mandatory for repositories that do not need it.

## Forbidden assumptions

List only repository-specific assumptions the reviewer must not make.

Examples:

- do not guess a Host endpoint;
- do not assume a platform was tested;
- do not infer a Cloudflare binding from another repository;
- do not treat device-local state as server-authoritative.

Keep this section small and tied to real repository contracts.
