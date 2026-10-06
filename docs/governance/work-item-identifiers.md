# Work Item Identifiers and Titles

Status: active Organization guidance.

This document defines the canonical Organization-wide, human-readable work-item identifier and title convention for repositories under `uichat-mira`.

It is the naming companion to [`source-of-truth.md`](source-of-truth.md) and [`work-item-lifecycle.md`](work-item-lifecycle.md). It does not create a second work-item ledger, Project field, or lifecycle system.

## 1. Purpose

Mira engineering work is currently discussed primarily by repository-local GitHub Issue numbers. That is ambiguous across repositories and makes cross-repository program work hard to reference by a stable name.

This convention provides one lightweight semantic identifier so work can be discussed by domain and sequence instead of by whichever repository happens to host the Issue.

The convention must:

- stay small and independently verifiable;
- work across repositories;
- preserve the already-proven Mobile `[MOB-NNN]` pattern;
- keep GitHub's native Issue identity authoritative;
- avoid turning naming into a second project-management system.

## 2. Canonical shape

For future conforming work items, use:

```text
[DOMAIN-NNN] Short human-readable title
```

Where:

- `DOMAIN` is one of the registered prefixes in section 3, written as 2–4 uppercase ASCII letters;
- `NNN` is a sequence of **at least three digits**, zero-padded, and is **Organization-wide within that domain**, not repository-local;
- exactly one space separates the identifier from the title.

Grammar:

```text
title      := identifier " " summary
identifier := "[" domain "-" sequence "]"
domain     := 2..4 UPPERCASE ASCII letters
sequence   := 3 or more ASCII digits
summary    := short human-readable title
```

Representative examples:

```text
[ORG-001] Establish human-readable work-item IDs
[AGT-001] Implement reusable external Worker
[DSK-001] Clarify Desktop runtime readiness
[MOB-076] <next conforming Mobile work item>
[WEB-001] ...
[FOL-001] ...
[OPS-001] ...
[SHY-001] ...
[REL-001] ...
```

The semantic ID is a **human coordination handle**. It does not replace the GitHub Issue, its URL, its repository, or its native Issue number.

## 3. Initial domain registry

The first governance version uses this deliberately small registry:

| Prefix | Domain | Typical current surfaces |
| --- | --- | --- |
| `ORG` | Organization governance and shared policy | Constitution, source-of-truth, work-item lifecycle, intake, shared governance rules |
| `AGT` | Agent / Tool / Harness / external Worker platform | Agent runtime, Tool governance, Worker dispatch, Worker evidence/provider work, Agent Benchmark while it remains part of this platform |
| `DSK` | Desktop-specific product/runtime | Desktop UI, shell, local runtime and Desktop-only behavior |
| `MOB` | Mobile product/runtime | Mobile UI/device/runtime and cross-repo work whose primary product outcome is Mobile |
| `WEB` | Mira public website/docs/content surfaces | Mira public docs/site and future public website work; not the Folio package itself |
| `FOL` | Folio publishing/runtime product | `@uichat-mira/folio`, schemas, runtime, package/site/release line |
| `OPS` | Organization operational/control-plane services | Control Room, observability, operational AI Review gateway/projections |
| `SHY` | Shiyan product/cloud service | Cross-client Shiyan contracts and Cloud Shiyan runtime; Mobile-only implementation refactors may remain `MOB` |
| `REL` | Remote Host relay/transport | Relay protocol/service and cross-repo transport work whose primary outcome is relay connectivity |

Do **not** add a `BEN` prefix. Current Benchmark work is part of the Agent platform and uses `AGT` unless it later becomes a genuinely independent product/capability domain.

## 4. Domain selection

The registry maps examples, not hard routing. Select the domain by the **primary outcome / contract owner**, not by the repository that happens to contain the Issue.

- a Mobile push feature may keep `MOB` even when Host/Broker implementation lives in Desktop;
- external Worker work in `.github` is `AGT`, not `ORG`;
- Organization AI Review policy is `ORG`, while Control Room runtime implementation is `OPS`;
- documentation about a Desktop subsystem remains `DSK`; work on the public Mira docs/site is `WEB`.

A repository name alone never determines the ID domain.

## 5. Adding a new domain

Adding a domain is a **governance change**, not an incidental decision made while opening one Issue.

A new domain should be added only when there is a stable product/capability identity expected to own multiple independent work items.

Do not create prefixes for a repository, team, technology, phase, release, temporary program, or one-off initiative merely because it exists.

When a new domain is genuinely justified, update this document's registry as part of the same governance change that introduces it.

## 6. Sequence allocation

For a new work item:

1. choose the domain from the registry by primary outcome/contract owner;
2. search current Organization Issues across repositories for conforming IDs in that domain;
3. take the highest simple numeric sequence and allocate the next number;
4. immediately before creation, verify that exact ID does not already exist;
5. immediately after creation, verify uniqueness again;
6. if a concurrent creation produced a collision, renumber the newly created work item to the next free sequence before implementation begins.

Do **not** create a separate mutable counter file, Project field, database, or task registry solely to allocate IDs.

For `MOB`, the existing simple sequence means the next new conforming ID starts after the highest current simple `MOB-NNN` value. Legacy compound IDs do not advance the simple sequence.

## 7. Collision handling

Allocation by Organization search is deliberately lightweight. Concurrent creation is the main race.

It is handled by **immediate post-create uniqueness verification**, not by a second counter ledger:

- if two work items intentionally or accidentally end up with the same `[DOMAIN-NNN]`, the later one is renumbered to the next free sequence;
- renumbering happens before implementation begins;
- the collision and the corrected ID are recorded on the affected Issue.

## 8. Cross-repository work

A semantic domain sequence is **shared across repositories**.

A single `[DOMAIN-NNN]` identifies one work item regardless of which repository hosts its Issue. The same domain's next number is allocated from the Organization-wide maximum, so two repositories cannot independently hand out the same ID.

Historical example: `MOB-056C-I1/I2/I3/I4` work spans Desktop and Mobile repositories while retaining the Mobile program identity. This confirms that human-readable IDs describe the stable product/capability domain, not the repository containing the Issue.

That compound grammar is **not** the template for new IDs; it is retained only as historical evidence for the cross-repository principle.

## 9. Legacy compatibility

- Existing simple Mobile IDs such as `MOB-071` through `MOB-075` are conformant. Their simple numeric sequence continues without reset.
- Historical compound forms such as `MOB-056C-I4` remain valid historical references, but they do **not** define future grammar and do **not** consume new simple sequence numbers.
- No historical Issue is renamed solely to satisfy this convention.
- No bulk rename or retroactive ID assignment is performed.

## 10. Relationship to GitHub-native identity and source of truth

GitHub's native reference remains authoritative for repository identity and the work-item contract:

```text
AGT-003  <->  uichat-mira/.github #40
```

- The semantic ID is a human coordination handle; it is **not** a second source of truth.
- For v1, the semantic ID is stored in the Issue **title**. No duplicate Project or custom field mirrors it.
- The GitHub Issue remains authoritative for the work-item contract and outcome, exactly as defined in [`source-of-truth.md`](source-of-truth.md).
- IDs do not encode hierarchy, lifecycle, priority, effort, dates, releases, environments, or repository identity.

## 11. Verification examples

These examples demonstrate the convention and its boundaries.

### 11.1 Current repository portfolio and domains

| Repository | Current role | Domain(s) in use |
| --- | --- | --- |
| `mira-desktop` | Desktop app/runtime; also hosts Agent, Tooling, Benchmark, Host and cross-repo integration work | `DSK`, `AGT` (by outcome) |
| `mira-mobile` | Mobile app/runtime and device capabilities | `MOB` |
| `.github` | Organization governance, shared Skills/workflows, work-item lifecycle, external Worker orchestration | `ORG`, `AGT` (by outcome) |
| `uichat-website` | Historical / currently inactive website repository | `WEB` if reactivated |
| `uichat-mira-docs` | Mira public documentation/site publishing | `WEB` |
| `control-room` | Organization observability, public read API/MCP, AI Review operational gateway | `OPS` |
| `folio` | Independent Git-native publishing/runtime package and official site | `FOL` |
| `cloud-shiyan` | Organization-owned Shiyan cloud runtime | `SHY` |
| `uichat-mira-relay` | Remote Host transport-only relay service | `REL` |

The dormant `uichat-website` repository does **not** create a needless extra domain. If it is reactivated, its work uses the existing `WEB` domain.

### 11.2 One domain spanning more than one repository

`MOB-056C-I1/I2/I3/I4` is historical evidence that one Mobile program identity can own work distributed across Desktop and Mobile repositories. The principle is preserved: a domain is selected by primary outcome, and its sequence is shared Organization-wide.

### 11.3 Coexistence with GitHub-native identity

```text
[AGT-003] Implement reusable external Worker   <->   uichat-mira/.github #40
```

The title carries the semantic handle; `uichat-mira/.github #40` remains the authoritative work-item identity. No Project/custom field ledger is introduced, so no second source of truth is created.

### 11.4 Dry run — same domain cannot intentionally receive the same ID

```text
Existing conforming AGT IDs found by Organization search:
  AGT-001, AGT-002, AGT-003
Highest simple sequence: 3
Next allocation: AGT-004

Work item A created as [AGT-004] ...
Work item B (same domain) must search again:
  AGT-001, AGT-002, AGT-003, AGT-004
Highest simple sequence: 4
Next allocation: AGT-005

If A and B are created concurrently and both claim AGT-004:
  - post-create uniqueness verification detects the duplicate;
  - the later item is renumbered to AGT-005 before implementation begins.
```

The convention therefore cannot intentionally assign the same semantic ID twice within a domain.

## 12. Non-goals

- No bulk rename of historical Issues.
- No retroactive assignment of IDs to every existing work item.
- No replacement of GitHub Issue numbers or URLs.
- No one-prefix-per-repository rule.
- No Jira-style hierarchy encoded into IDs.
- No continuation of compound child encodings such as `-I1`, `-A`, or release/phase suffixes for new work.
- No Priority, Status, Effort, owner, release, date, environment, or lifecycle encoded into an ID.
- No large prefix taxonomy.
- No Project database, custom task registry, or counter service.
- No automatic mutation of old PR titles, commits, branches, or documentation merely to match the convention.
