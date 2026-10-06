# Human-Readable Work Item IDs

Status: active Organization guidance.

This document defines the Organization-wide human-readable work-item identifier and title convention. It is a naming and coordination contract. It is not a second work-item ledger, Project field, counter service, or task registry.

Use it together with:

- [`source-of-truth.md`](source-of-truth.md) for what owns work-item contract and outcome;
- [`work-item-lifecycle.md`](work-item-lifecycle.md) for Project lifecycle position;
- [`../../skills/create-work-item/SKILL.md`](../../skills/create-work-item/SKILL.md) for creation authority and procedure.

## 1. Purpose

Mira engineering work should be discussable by a stable semantic handle instead of relying only on repository-local GitHub Issue numbers. The convention exists so that:

- work spanning repositories can share one recognizable program/domain identity;
- humans can refer to work compactly in conversation, branches, and docs;
- the handle stays lightweight and does not grow into a second project-management system.

The convention does not replace the GitHub Issue, its number, or its URL.

## 2. Identifier grammar and title shape

For conforming work items, use:

```text
[DOMAIN-NNN] Short human-readable title
```

Rules:

- **`DOMAIN`** is an uppercase prefix from the canonical registry in section 3.
- **`NNN`** is a sequence number of at least three digits. It is Organization-wide within that domain, not repository-local.
- The ID starts the Issue **title**, in square brackets, followed by a space and a short human-readable title.
- For v1 the semantic ID is stored only in the Issue title. Do not add a duplicate Project field or custom field merely to mirror it unless a later, proven consumer requires a machine-readable projection.

An ID must **not** encode:

- hierarchy or parent/child relationships;
- lifecycle, status, or Phase;
- priority, effort, owner, or dates;
- release, version, environment, or milestone;
- repository identity.

### Examples

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

## 3. Initial domain registry

The first governance version uses this deliberately small registry. Do not grow it casually.

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

There is deliberately **no `BEN`** prefix. Current Benchmark work is part of the Agent platform and uses `AGT` unless Benchmark later becomes a genuinely independent product/capability domain.

## 4. Domain selection by primary outcome

Domain selection follows the **primary outcome / contract owner**, not the repository that happens to contain the Issue. The repository-to-prefix examples in section 5 are illustrative, not hard routing.

Examples of the principle:

- a Mobile push feature may keep `MOB` even when Host/Broker implementation lives in Desktop;
- external Worker work in `.github` is `AGT`, not `ORG`;
- Organization AI Review policy is `ORG`, while Control Room runtime implementation is `OPS`;
- documentation about a Desktop subsystem remains `DSK`; work on the public Mira docs/site is `WEB`.

`.github` is the Organization's governance and shared-automation repository, not a semantic domain. An Issue opened in `.github` is **not** automatically classified as `ORG`.

## 5. Portfolio mapping examples

The current Organization portfolio maps to domains by primary outcome, not mechanically by repository name.

| Repository | Current role | Naming implication |
| --- | --- | --- |
| `mira-desktop` | Desktop app/runtime; also hosts Agent, Tooling, Benchmark, Host and cross-repo integration work | Repository name alone cannot determine the ID domain |
| `mira-mobile` | Mobile app/runtime and device capabilities | Existing `MOB-xxx` sequence is the strongest proven convention and should be preserved |
| `.github` | Organization governance, shared Skills/workflows, work-item lifecycle, external Worker orchestration | Needs both Organization-governance and Agent/Worker domains; `.github` itself is not a semantic domain |
| `uichat-website` | Historical / currently inactive website repository | Should not force a dedicated new domain; future website work can use `WEB` |
| `uichat-mira-docs` | Mira public documentation/site publishing | Belongs to the public-web/content surface rather than requiring a repo-derived prefix |
| `control-room` | Organization observability, public read API/MCP, AI Review operational gateway | Distinct operational/control-plane domain |
| `folio` | Independent Git-native publishing/runtime package and official site | Stable product/runtime identity merits its own domain |
| `cloud-shiyan` | Organization-owned Shiyan cloud runtime | Stable Shiyan product/service domain |
| `uichat-mira-relay` | Remote Host transport-only relay service | Stable transport/relay domain |

A dormant repository such as `uichat-website` does **not** create a needless extra domain. If it is reactivated, its work can use `WEB`.

## 6. Adding a new domain

Add a domain only when there is a **stable product/capability identity expected to own multiple independent work items**.

Do not create a prefix for:

- a repository;
- a team or individual;
- a technology;
- a phase, release, or temporary program;
- a one-off initiative.

Adding a domain is a governance change, not an incidental decision made while opening a single Issue. Update this registry and get maintainer agreement before allocating IDs in a new prefix.

## 7. Sequence allocation

For a new work item:

1. choose the domain from the canonical registry by primary outcome/contract owner;
2. search Organization Issues across repositories and **all states** for conforming IDs in that domain;
3. take the highest simple numeric sequence and allocate the next number;
4. immediately before creation, verify that the exact ID does not already exist;
5. immediately after creation, verify uniqueness again;
6. if a concurrent creation produced a collision, renumber the newly created work item to the next free sequence before implementation begins.

Do not create a separate mutable counter file, Project field, database, or task registry solely to allocate IDs. Allocation is deliberately lightweight and search-based.

### Permanent occupancy

Semantic IDs are **permanently occupied once used**. Allocation and uniqueness checks must search Organization Issues across **all states**, including open, closed/completed, duplicate, and not-planned. Once an ID has belonged to any Issue, it is never reused, even after that Issue becomes inactive.

### Do not reuse an existing Issue's ID

If a requested conforming ID already belongs to an existing Issue, do not create another Issue with the same ID. **Use that existing Issue instead.** A maintainer-supplied semantic ID may be used for a new Issue only when it is valid for the selected domain and currently unoccupied Organization-wide.

## 8. Collision handling

Concurrent creation is the main race. The search-based allocator cannot guarantee absolute prevention of simultaneous duplicate issuance. It detects and corrects races through the post-create uniqueness verification in section 7:

- if the new Issue's ID is already occupied, the newly created work item is renumbered to the next free sequence;
- renumbering happens before implementation begins;
- no counter ledger is introduced to make the race impossible.

### Worked example: two new work items in the same domain

Suppose the highest in-use `AGT` sequence is hypothetically `100`, and two new Agent/Worker work items are created at nearly the same time. Both would compute the next free ID as `AGT-101`:

```text
Worker A creates [AGT-101] ...   post-create check: AGT-101 unoccupied -> keep
Worker B creates [AGT-101] ...   post-create check: AGT-101 now occupied
                                 -> renumber the new Issue to AGT-102
```

The two new work items cannot intentionally keep the same semantic ID: whichever is verified second is detected as a collision and renumbered before implementation begins.

## 9. Cross-repository work

The domain describes the stable product/capability identity, not the repository holding the Issue. The same domain sequence is therefore shared across repositories.

Existing history proves the principle: `MOB-056C-I1`, `MOB-056C-I2`, `MOB-056C-I3`, and `MOB-056C-I4` work spans the Desktop and Mobile repositories while retaining the Mobile program identity. That compound grammar is **historical evidence only**; it is not the template for new IDs.

## 10. Legacy compatibility

- Existing simple Mobile IDs such as `MOB-071` through `MOB-075` are already conformant. Their simple numeric sequence continues without reset: the next new conforming Mobile ID starts after the highest current simple `MOB-NNN` value.
- Historical compound forms such as `MOB-056C-I4` remain valid historical references. They do **not** define future grammar and do **not** consume new simple sequence numbers.
- Historical Issues remain referenced by their native `repo/#number` unless they already carried a semantic ID. Do not retroactively assign semantic IDs to historical Issues, and do not rename old Issues, PR titles, commits, branches, or documentation merely to match this convention.

## 11. Relationship to GitHub-native identity and source of truth

The semantic ID is a **human coordination handle**. It does not replace the GitHub Issue, its URL, its repository, or its native Issue number.

GitHub's native reference remains authoritative for repository identity and work-item existence. For example, a historical Issue such as `uichat-mira/.github #40` is referenced by its native repository and number because it predates this convention and has no semantic ID.

A hypothetical new work item would carry a semantic ID of its own:

```text
[AGT-NNN] <hypothetical new Agent/Worker work item>
   stored in the title of a new Issue, e.g. uichat-mira/.github #NNN
```

The semantic ID belongs to that new Issue. It does not reassign or rename `uichat-mira/.github #40`, and it does not create a second source of truth: the Issue remains authoritative for the work-item contract and outcome, as defined in [`source-of-truth.md`](source-of-truth.md).

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

## Working rule

```text
[DOMAIN-NNN]        = human coordination handle, stored in the Issue title
DOMAIN              = stable product/capability domain, not the repository
NNN                 = Organization-wide simple sequence within the domain
GitHub Issue/#/URL  = authoritative work-item identity and contract
Occupancy           = permanent once used, checked across all Issue states
Allocation          = search highest simple sequence, pre/post-create checks
Race                = detected and corrected by renumbering, not by a counter
```
