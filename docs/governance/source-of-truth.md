# Source of Truth

Mira uses different sources of truth for different kinds of information. The goal is to avoid one document pretending to be authoritative for everything.

## 1. Code and runtime state

For questions such as:

- what code exists now;
- what branch currently contains a change;
- what workflow actually runs;
- what configuration is active;
- what is currently deployed;

the real repository, workflow configuration, and deployed runtime state are authoritative.

Documentation must not override observable reality.

## 2. GitHub Issue — work-item truth

An Issue is the engineering source of truth for a work item.

It should carry the information needed to understand and accept that unit of work, including as appropriate:

- problem or goal;
- scope;
- constraints;
- acceptance criteria;
- decisions;
- current status;
- links to implementation or verification evidence.

If the implementation changes the agreed scope, update the Issue rather than leaving the decision only in chat.

## 3. Organization docs — policy and SOP truth

The `uichat-mira/.github` repository is the source of truth for organization-wide engineering policy and reusable SOPs.

Examples:

- environment model;
- repository migration procedure;
- release policy;
- shared development conventions.

Repository-specific rules may extend these documents. If a repository must diverge, document the exception locally and explain why.

## 4. GitHub Project — management view

GitHub Project is a management projection over work items.

It may organize Issues by:

- priority;
- owner;
- stage;
- milestone;
- release;
- migration status.

Project fields are useful for planning and visibility, but they must not silently replace the Issue's scope or acceptance criteria.

## 5. mira.tomz.io — public projection

The website is the public projection of Mira's state, direction, development journal, and selected roadmap information.

It is not the engineering source of truth.

Public content should be derived from verified internal state rather than becoming a second independent planning system.

## Conflict rule

When two sources disagree, first identify what kind of truth is in conflict.

Use this order:

1. actual code/config/runtime for current technical reality;
2. Issue for the agreed state of a specific work item;
3. organization/repository docs for policy and procedure;
4. Project for management presentation;
5. website for public presentation.

Then repair the stale projection instead of forcing reality to match an outdated document.

## Working rule

```text
Issue = work item
Project = management view
mira.tomz.io = public projection
.github/docs = organization policy and SOP
repo/config/runtime = current technical reality
```

Each layer has one job. Avoid maintaining the same decision independently in several places.
