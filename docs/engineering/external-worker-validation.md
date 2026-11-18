# External Worker Validation Profiles

Status: active Organization contract for External Worker profile-mode validation.

This document owns the **Validation Profile schema, dispatch ceiling, execution order, and structured Validation Report contract**. It does not redefine the Organization test layers in [testing-standard.md](testing-standard.md), and it does not own Return-to-Worker behavior.

Concrete commands belong to the caller repository at the exact Candidate base SHA in:

```text
.github/mira-validation-profiles.json
```

The reusable Worker owns only how that repository-defined profile is selected, bounded, executed, and reported.

## 1. Core rule

Validation answers:

> Does this exact Candidate have the evidence required by this work-item contract to enter Delivery?

It does **not** mean "run every available check".

The executor must use the lowest sufficient evidence and must never silently escalate to a more expensive tier because a cheaper capability is absent or failed.

## 2. Ladder

The Validation Ladder maps execution cost/risk to the existing Organization testing language.

| Tier | Responsibility | Typical evidence |
| --- | --- | --- |
| L0 | Candidate identity / contract integrity | exact base, patch/tree, contract fingerprint |
| L1 | cheap mechanical/static | `git diff --check`, targeted format/lint/static checks |
| L2 | targeted behavior / contract | focused unit and contract tests |
| L3 | relevant runtime integration | selected runtime/component integration |
| L4 | expensive platform/build/E2E | package, installer, native/platform build, environment E2E |
| L5 | release / production | release-specific evidence and production smoke |

This ladder does not replace T1–T5. A repository profile should choose commands that implement the relevant Organization testing responsibilities for that repository.

L4/L5 are never inferred from the presence of a build script. They run only when the selected repository profile contains them **and** the dispatch ceiling explicitly permits them.

## 3. Repository profile schema

Example:

```json
{
  "schema_version": 1,
  "profiles": {
    "feature-fast": {
      "description": "Ordinary feature/repair validation",
      "checks": [
        {
          "id": "static",
          "tier": "L1",
          "requirement": "required",
          "command": "pnpm lint",
          "failure_result": "REPAIR"
        },
        {
          "id": "contracts",
          "tier": "L2",
          "requirement": "required",
          "command": "pnpm test:contract",
          "failure_result": "REPAIR"
        },
        {
          "id": "package",
          "tier": "L4",
          "requirement": "not_applicable"
        }
      ]
    }
  }
}
```

Rules:

- profile/check IDs use `[A-Za-z0-9._-]` and must be unique inside one profile;
- L0 is reserved for the trusted Candidate restore boundary and cannot be supplied by a repository profile;
- repository checks use L1–L5;
- at most 24 checks are allowed in one profile;
- commands are bounded to 4096 characters;
- checks are executed in tier order, preserving repository order inside one tier;
- profile content is read from the **exact Candidate base SHA before Candidate restore**. A Worker cannot authorize a new command by modifying the profile inside its Candidate.
- profile-mode checks must not mutate tracked or non-ignored Candidate state. If a check changes that state, Validation returns `BLOCKED`; later checks do not run. Validation logs/evidence live outside the Candidate workspace.

### Requirement

Each check declares one of:

- `required` — must execute and pass for the profile to be complete;
- `optional` — executes when allowed, but failure/unavailability does not reject an otherwise sufficient Candidate;
- `not_applicable` — explicitly not required for this profile and must not contain or execute a command.

### Failure classification

A required executed check may declare:

- `REPAIR` — Candidate code/behavior should be corrected;
- `BLOCKED` — the failure is not safely interpreted as a code repair.

Default is `REPAIR`.

The executor does not inspect prose logs to guess another classification.

## 4. Dispatch contract

Reusable Worker inputs:

- `validation_profile` — optional repository profile name;
- `validation_max_tier` — hard ceiling for profile mode; default `L3`;
- `verification_command` — legacy compatibility path only when `validation_profile` is empty.

Before provider/model setup, the Worker resolves a `validation-contract.json` from the exact base. A missing/invalid requested profile, invalid max tier, or empty legacy contract is rejected **before model execution** with an explicit `VALIDATION_GAP` or `BLOCKED` dispatch result. This is a dispatch-contract failure, not a Candidate failure.

A profile-mode dispatch may run only checks declared by the selected repository profile and at/below the requested ceiling.

The ceiling is monotonic:

> it can prevent expensive work; it cannot cause the executor to invent or escalate work.

Examples:

- profile contains L4 but dispatch ceiling is L2 → L4 does not run;
- a required L4 is above an L2 ceiling → `VALIDATION_GAP`, not automatic L4;
- an optional L4 is above an L2 ceiling → skipped, without upgrading the run;
- unknown profile/profile file → `VALIDATION_GAP`;
- required command/capability unavailable → `VALIDATION_GAP`.

## 5. Fail-fast

Validation runs cheap checks before expensive checks.

When a required check returns `REPAIR` or `BLOCKED`, later executable checks are skipped. A failed L1/L2 check must therefore prevent an L4 package/E2E command from starting.

A gap caused by the dispatch ceiling also never relaxes that ceiling.

## 6. Validation Report

Verify emits a bounded machine-readable `validation-report.json`.

Top-level result is exactly one of:

- `PASS` — every required check allowed by the contract executed and passed; no required evidence is missing;
- `REPAIR` — a required code/behavior check rejected the Candidate;
- `BLOCKED` — identity/contract/runtime conditions prevent safe validation or repair classification;
- `VALIDATION_GAP` — required evidence could not be executed or was explicitly prevented by the dispatch ceiling.

The report records:

- mode (`profile` or `legacy`);
- profile and max tier where applicable;
- profile identity/hash;
- ordered checks;
- tier and requirement;
- command/capability;
- status, exit code and duration;
- skipped/not-applicable state;
- failure classification;
- explicit gaps.

Only `PASS` authorizes ordinary Delivery.

A report is evidence, not Issue acceptance.

The bounded repair lifecycle preserves the distinction: `REPAIR` may enter [Return-to-Worker](external-worker-repair.md); `BLOCKED` and `VALIDATION_GAP` do not automatically invoke another model under the same validation contract. The repair lifecycle may not reinterpret these results from raw logs.

## 7. Legacy compatibility

When `validation_profile` is empty, the Worker preserves the existing `verification_command` path:

- the exact caller command still runs once after Candidate identity and `git diff --check`;
- `validation_max_tier` is ignored;
- the report marks the command `legacy-unclassified` because the Worker cannot honestly infer its real cost/test layer from an arbitrary shell string;
- existing Candidate Recovery keeps the legacy `mira-contract-v2` fingerprint shape.

New Foreman/Workforce dispatch should use profile mode. Legacy mode is a migration surface, not a model for new scheduling.

## 8. Recovery identity

Profile-mode Recovery binds Candidate compatibility to:

- profile name;
- dispatch max tier;
- normalized selected-profile contract identity.

A changed profile or ceiling is therefore contract drift for Recovery. An old Candidate is not silently treated as verified under a new validation contract.

Legacy callers retain the existing verification-command hash contract during migration.

## 9. Non-goals

This contract does not:

- own Return-to-Worker state or repair-round limits; [External Worker Bounded Return-to-Worker](external-worker-repair.md) owns that loop;
- choose tests for a repository;
- reinterpret T1–T5;
- automatically run full Desktop packaging, device checks, T4/T5, release or production smoke;
- let a model/Foreman inject arbitrary validation commands;
- turn a green Validation Report into merge, acceptance, release or deployment authority.
