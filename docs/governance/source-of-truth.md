# Source of Truth

Mira uses different sources of truth for different kinds of information. The goal is to avoid one surface pretending to be authoritative for everything.

## 1. Code and runtime state

For questions such as:

- what code exists now;
- what branch currently contains a change;
- what workflow actually runs;
- what configuration is active;
- what is currently deployed;

the real repository, workflow configuration, and deployed runtime state are authoritative.

Documentation must not override observable reality.

## 2. GitHub Issue — work-item contract and outcome

An Issue is the engineering source of truth for one work item.

It should carry the information needed to understand and accept that unit of work, including as appropriate:

- problem or goal;
- scope and non-goals;
- constraints;
- acceptance criteria;
- decisions that change the contract;
- links to implementation or verification evidence;
- final open/closed state and close reason.

If implementation changes the agreed scope, update the Issue rather than leaving the decision only in chat, a PR, or a Project field.

Do not maintain a prose copy of Project Status, Priority, Effort, dates, assignees, linked PRs, or other metadata that GitHub already owns elsewhere.

Issue truth and Issue mutation authority are different concepts. The Issue is authoritative for its current contract/outcome, but creating, accepting, closing, declining, duplicating, or reopening it still requires authority from the current maintainer instruction or applicable contract. Observable completion evidence does not grant that authority by itself.

## 3. Organization Issue Fields — structured management metadata

Organization Issue Fields own cross-repository structured metadata such as:

- Priority;
- Effort;
- Start date;
- Target date.

Their current field values are authoritative for those metadata values. Do not duplicate them in the Issue body or create competing Project-only copies without a demonstrated need.

Organization Issue Fields are not the work-item lifecycle. Lifecycle position belongs to native Project `Status` under [`work-item-lifecycle.md`](work-item-lifecycle.md).

## 4. Organization docs — policy and SOP truth

The `uichat-mira/.github` repository is the source of truth for organization-wide engineering policy and reusable SOPs.

Examples:

- work-item creation and closure authority/procedure;
- work-item lifecycle;
- environment model;
- testing standard;
- repository migration procedure;
- release policy;
- shared development conventions.

Repository-specific rules may extend these documents. If a repository must diverge, document the exception locally and explain why.

## 5. GitHub Project — management projection

`Mira Development` is a management projection over work items.

Its native `Status` answers only the coarse workflow-position question:

```text
Todo | In Progress | Done
```

It may also surface Organization Issue Fields and GitHub-owned relationships such as assignees, linked pull requests, repository, milestone, timestamps, and sub-issue progress.

Project Status must not silently replace Issue scope or acceptance criteria, and it must not duplicate CI/review/environment state. `Done` means the Project item is inactive; the Issue close reason determines whether work was completed, not planned, or duplicated.

If Project Status is stale while the Issue/runtime evidence is clear, repair the management projection according to the lifecycle contract. Do not rewrite technical reality or Issue acceptance to make the board look consistent.

## 6. Pull requests, review, and CI — implementation evidence

Pull requests, review results, CI checks, builds, and test runs are evidence about implementation and verification.

They do not become a second work-item ledger and do not automatically accept an Issue. A merge or green check proves only what that event/check actually establishes.

Evidence can support an authorized acceptance decision; it does not create acceptance or closure authority.

## 7. Environment state

The branch/environment model `feat/* -> dev -> test -> prod` owns environment position and promotion semantics.

Project Status must not be used as an alias for `dev`, `test`, or `prod`. Environment evidence remains attached to the exact branch, deployment, version, or release that was actually verified.

Closing an Issue does not itself authorize environment promotion or release.

## 8. mira.tomz.io — public projection

The website is the public projection of Mira's state, direction, development journal, and selected roadmap information.

It is not the engineering source of truth.

Public content should be derived from verified internal state rather than becoming a second independent planning system.

## Conflict rule

When two sources disagree, first identify what kind of truth is in conflict.

Use the owner of that concept:

- current technical reality -> code / configuration / workflow / runtime;
- work-item contract and outcome -> Issue;
- structured planning metadata -> Organization Issue Fields;
- Organization procedure -> Organization docs;
- management workflow position -> Project Status;
- implementation/verification evidence -> PR / review / CI;
- environment position -> branch/deployment/release evidence;
- public presentation -> website.

Then repair the stale projection instead of forcing one concept to imitate another.

Authority conflicts are resolved by the instruction-priority model in `AGENTS.md`, not by whichever source currently looks most complete.

## Working rule

```text
Issue              = work-item contract + outcome
Project Status     = Todo / In Progress / Done management position
Org Issue Fields   = Priority / Effort / dates and similar metadata
PR / Review / CI   = implementation + verification evidence
feat/dev/test/prod = environment position
.github/docs       = Organization policy and SOP
repo/config/runtime= current technical reality
mira.tomz.io       = public projection
```

Each layer has one job. Avoid maintaining the same decision independently in several places.
