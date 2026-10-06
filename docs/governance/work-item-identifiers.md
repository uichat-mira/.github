# Work Item Identifiers

Status: active Organization guidance.

This document defines the canonical, human-readable identifier and title convention for Mira engineering work items. It is a coordination handle that lets people discuss work by stable semantic IDs instead of relying primarily on repository-local GitHub Issue numbers.

The convention is deliberately lightweight. It is not a second project-management system, ledger, or lifecycle.

Use [`../../skills/create-work-item/SKILL.md`](../../skills/create-work-item/SKILL.md) for the creation procedure, [`source-of-truth.md`](source-of-truth.md) for source-of-truth boundaries, and [`work-item-lifecycle.md`](work-item-lifecycle.md) for lifecycle position.

## 1. Canonical shape

For future conforming work items, use:

```text
[DOMAIN-NNN] Short human-readable title
```

Rules:

- `DOMAIN` is one of the registered uppercase domain prefixes in [section 2](#2-initial-domain-registry).
- `NNN` is a simple numeric sequence, zero-padded to at least three digits. It is **Organization-wide within that domain**, not repository-local. A domain that exceeds `999` may use additional digits.
- The bracketed ID is the first token of the GitHub Issue title, followed by one space and a short human-readable title.
- The ID describes the stable product/capability domain. It must not encode repository identity, hierarchy, lifecycle, priority, effort, dates, release, environment, phase, or sequence of a new project-management system.

Examples:

```text
[ORG-001] Establish human-readable work-item IDs
[AGT-001] Implement reusable external Worker
[DSK-001] Clarify Desktop runtime readiness
[MOB-076] <next conforming Mobile work item>
[WEB-001] Publish updated public documentation
[FOL-001] Add schema validation to the Folio runtime
[OPS-001] Expose a Control Room read API
[SHY-001] Define the Shiyan cross-client contract
[REL-001] Harden relay transport reconnection
```

## 2. Initial domain registry

The first governance version uses this deliberately small registry:

| Prefix | Domain | Typical current surfaces |
| --- | --- | --- |
| `ORG` | Organization governance and shared policy | Constitution, source-of-truth, work-item lifecycle, intake, shared governance rules |
| `AGT` | Agent / Tool / Harness / external Worker platform | Agent runtime, Tool governance, Worker dispatch, Worker evidence/provider work, Agent Benchmark while it remains part of this platform |
| `DSK` | Desktop-specific product/runtime | Desktop UI, shell, local runtime, and Desktop-only behavior |
| `MOB` | Mobile product/runtime | Mobile UI/device/runtime and cross-repo work whose primary product outcome is Mobile |
| `WEB` | Mira public website/docs/content surfaces | Mira public docs/site and future public website work; not the Folio package itself |
| `FOL` | Folio publishing/runtime product | `@uichat-mira/folio`, schemas, runtime, package/site/release line |
| `OPS` | Organization operational/control-plane services | Control Room, observability, operational AI Review gateway/projections |
| `SHY` | Shiyan product/cloud service | Cross-client Shiyan contracts and Cloud Shiyan runtime; Mobile-only implementation refactors may remain `MOB` |
| `REL` | Remote Host relay/transport | Relay protocol/service and cross-repo transport work whose primary outcome is relay connectivity |

Do **not** add `BEN` in the initial registry. Current Benchmark work is part of the Agent platform and uses `AGT` unless it later becomes a genuinely independent product/capability domain.

## 3. Domain selection follows the outcome

Domain selection follows the **primary outcome / contract owner**, not the repository that happens to contain the Issue.

Repository-to-prefix mappings in this document are examples, not hard routing. Examples:

- a Mobile push feature may keep `MOB` even when Host/Broker implementation lives in Desktop;
- external Worker work in `.github` is `AGT`, not `ORG`;
- Organization AI Review policy is `ORG`, while Control Room runtime implementation is `OPS`;
- documentation about a Desktop subsystem remains `DSK`; work on the public Mira docs/site is `WEB`.

`.github` is not a semantic domain. The repository hosts both Organization governance (`ORG`) and Agent/Worker platform (`AGT`) work, so the Issue outcome decides the prefix.

## 4. Portfolio mapping examples

The initial registry covers the current Organization portfolio. These are representative mappings, not a routing rule.

| Repository | Current role | Typical domain(s) | Example conforming ID |
| --- | --- | --- | --- |
| `mira-desktop` | Desktop app/runtime; also hosts Agent, Tooling, Benchmark, Host and cross-repo integration work | `DSK` for Desktop-only outcomes; `AGT` for Agent/Worker platform outcomes; `MOB` for cross-repo work whose primary outcome is Mobile | `[DSK-001] Clarify Desktop runtime readiness` |
| `mira-mobile` | Mobile app/runtime and device capabilities | `MOB` | `[MOB-076] <next conforming Mobile work item>` |
| `uichat-mira/.github` | Organization governance, shared Skills/workflows, work-item lifecycle, external Worker orchestration | `ORG` for governance; `AGT` for Agent/Worker platform | `[ORG-001] ...`, `[AGT-001] ...` |
| `uichat-website` | Historical / currently inactive website repository | `WEB` if reactivated; no dedicated new domain | `[WEB-001] ...` |
| `uichat-mira-docs` | Mira public documentation/site publishing | `WEB` | `[WEB-001] Publish updated public documentation` |
| `control-room` | Organization observability, public read API/MCP, AI Review operational gateway | `OPS` | `[OPS-001] Expose a Control Room read API` |
| `folio` | Independent Git-native publishing/runtime package and official site | `FOL` | `[FOL-001] Add schema validation to the Folio runtime` |
| `cloud-shiyan` | Organization-owned Shiyan cloud runtime | `SHY` | `[SHY-001] Define the Shiyan cross-client contract` |
| `uichat-mira-relay` | Remote Host transport-only relay service | `REL` | `[REL-001] Harden relay transport reconnection` |

The dormant `uichat-website` repository does not justify an extra domain. If website work resumes, it uses `WEB` alongside the public docs/site surface.

## 5. Cross-repository work

A semantic domain is not owned by one repository. The same domain sequence is shared across repositories.

The decisive precedent is `MOB-056C-I1/I2/I3/I4`, whose work spans Desktop and Mobile while retaining the Mobile program identity. Human-readable IDs must therefore describe the stable product/capability domain, not the repository containing the Issue:

```text
MOB-056C-I1/I2/I3/I4  spans mira-desktop and mira-mobile
                      -> domain is Mobile; repository is not the domain
```

Historical compound forms such as `MOB-056C-I4` remain valid **historical references**, but their grammar (`-I1`, `-A`, release/phase/child suffixes) is not the template for new IDs. New cross-repository work uses one domain and one Organization-wide sequence.

## 6. Sequence allocation

For a new work item:

1. choose the domain from the canonical registry by primary outcome/contract owner;
2. search current Organization Issues across repositories for conforming IDs in that domain;
3. take the highest simple numeric sequence and allocate the next number;
4. immediately before creation, verify that exact ID does not already exist;
5. immediately after creation, verify uniqueness again;
6. if a concurrent creation produced a collision, renumber the newly created work item to the next free sequence before implementation begins.

Do not create a separate mutable counter file, Project field, database, or task registry solely to allocate IDs. Allocation is by Organization-wide search.

For `MOB`, the next new conforming ID starts after the highest current simple `MOB-NNN` value. Legacy compound IDs do not advance the simple sequence.

### Worked allocation example

Illustrative walkthrough (a rule demonstration, not an executed allocation):

1. Two governance work items are proposed at roughly the same time; both select `ORG` by primary outcome.
2. The highest conforming `ORG` ID currently visible Organization-wide is `ORG-004`, so both proposals initially compute `ORG-005`.
3. The first item is created as `[ORG-005] ...`. The second item's pre-create check now finds `ORG-005`, so it allocates `ORG-006`.
4. If both are created before either pre-create check observes the other, the post-create uniqueness check detects two `[ORG-005]` titles. The later item is renumbered to the next free sequence (`ORG-006`) and re-verified before implementation begins.

Result: two work items in the same domain cannot intentionally share a semantic ID, and no counter ledger is required.

## 7. Collision handling

Two new work items in the same domain must not intentionally receive the same semantic ID. Because allocation is by search rather than a counter, concurrent creation is the main race.

The pre-create check (section 6, step 4) removes most races. The post-create uniqueness check (section 6, step 5) is the backstop. When a collision is detected:

1. renumber the newly created work item to the next free sequence;
2. re-verify that the new ID is unique;
3. only then begin implementation.

Renumbering changes only the Issue title. It does not create a second ledger, and it does not change the GitHub Issue, its URL, or its native number. If a collision cannot be safely renumbered, report the collision instead of leaving two items with the same semantic ID.

## 8. Adding a new domain

Adding a domain is a governance change, not an incidental decision made while opening one Issue.

Add a prefix only when there is a stable product/capability identity expected to own multiple independent work items. Do not create prefixes for a repository, team, technology, phase, release, temporary program, or one-off initiative merely because it exists.

To add a domain: update the registry in this document, then update any creation surface that references it (currently [`../../skills/create-work-item/SKILL.md`](../../skills/create-work-item/SKILL.md) and [`../../.github/ISSUE_TEMPLATE/work-item.yml`](../../.github/ISSUE_TEMPLATE/work-item.yml)). Do not introduce a counter service or Project field to support the new prefix.

## 9. Legacy compatibility

- Existing simple Mobile IDs such as `MOB-071` through `MOB-075` are conformant. Their simple numeric sequence continues without reset.
- Historical compound forms such as `MOB-056C-I4` remain valid historical references, but they do not define future grammar and do not consume new simple sequence numbers.
- No bulk rename of historical Issues, and no retroactive assignment of IDs to every existing work item.
- Do not mutate old PR titles, commits, branches, or documentation merely to match the convention.

## 10. Relationship to GitHub-native identity

GitHub's native reference remains authoritative for repository identity:

```text
AGT-003  <->  uichat-mira/.github #40
```

The semantic ID is a **human coordination handle** stored in the Issue title for v1. It does not replace the GitHub Issue, URL, repository, or native Issue number.

For v1, do **not** add a duplicate Project/custom field to mirror the semantic ID. If a later proven machine-readable consumer requires projection, that is a separate, explicitly authorized governance decision.

`[ORG-001]` and `uichat-mira/.github #40` can coexist without creating a second source of truth: the Issue remains authoritative for the work-item contract and outcome, and the semantic ID remains a title-level handle.

Follow [`source-of-truth.md`](source-of-truth.md) when these surfaces appear to disagree.

## 11. Non-goals

- No bulk rename of historical Issues or retroactive assignment of IDs to existing work items.
- No replacement of GitHub Issue numbers or URLs.
- No one-prefix-per-repository rule.
- No Jira-style hierarchy encoded into IDs.
- No compound child encodings such as `-I1`, `-A`, or release/phase suffixes for new work.
- No Priority, Status, Effort, owner, release, date, environment, or lifecycle encoded into an ID.
- No large prefix taxonomy.
- No Project database, custom task registry, or counter service.
- No automatic mutation of old PR titles, commits, branches, or documentation merely to match the convention.
