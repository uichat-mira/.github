# Mira Organization AI Review Output Contract

Contract version: `mira-ai-review-output/v1`

This contract defines the normalized review result Mira owns independently of the review provider.

## Published identity

A published Organization review uses this marker exactly once:

```text
<!-- mira-ai-review:v1 -->
```

The deterministic runtime / publisher, not the model, must attach review metadata that identifies the exact review input and execution identity.

At minimum the metadata records:

- repository;
- PR number;
- head SHA;
- base SHA;
- provider / engine;
- model when applicable;
- Organization policy identity;
- repository profile identity when applicable;
- runtime version.

Repository profiles may require an additional compatibility marker during migration. For example, Mobile may retain its existing marker while it is being migrated; Organization normalization must not silently remove a repository contract.

## Required logical sections

Every review result must contain these logical sections, regardless of provider-specific rendering:

1. Verdict
2. Findings
3. Validation gaps
4. Review metadata

A repository profile may add sections such as platform/surface notes or local handoff instructions.

## Verdict

The verdict is exactly one of:

```text
NO_BLOCKING_FINDINGS
CHANGES_NEEDED
HUMAN_CHECK_NEEDED
CONTRACT_CONFLICT
```

`PASS`, `APPROVED`, `LGTM`, or similar acceptance language is not a normalized Mira verdict.

## Findings

Only high-confidence P0-P2 findings are normally published.

Each actionable finding contains at least:

```text
Severity
Observation
Inference
Judgment
Impact
Location
Suggested Fix
Verification
```

Rules:

- Observation states directly supported evidence.
- Inference states the derived behavior or causal conclusion.
- Judgment states why that behavior is a defect at the stated severity.
- Impact names the concrete affected behavior, user, system, security, release, or maintenance consequence.
- Location identifies the smallest useful changed location or related locations.
- Suggested Fix describes the required correction direction without forcing an unrelated redesign.
- Verification describes how the Builder / Maintainer can prove the issue is resolved.
- One root cause spanning multiple files is one finding, not repeated findings.
- Existing base-only issues that the PR does not introduce or worsen are omitted as blocking findings by default.
- Secrets or credential values must never be reproduced.

When no high-confidence P0-P2 issue is established, Findings must explicitly say so rather than inventing low-confidence concerns.

## Validation gaps

Validation gaps contain material evidence that was unavailable or not performed and that affects confidence or acceptance.

Examples include device checks, external service interoperability, permissions, signing, provider behavior, environment-specific behavior, or diff/context limits.

A missing check is not automatically a defect.

If there is no meaningful gap, state that none was identified.

## CONTRACT_CONFLICT

When the verdict is `CONTRACT_CONFLICT`, the result must identify:

- the conflicting contract sources;
- the smallest conflicting statements or requirements that can be safely summarized;
- why the conflict changes the review judgment;
- the Maintainer decision required to resume a reliable review.

Do not select a preferred contract by generic best practice when the defined precedence does not resolve the conflict.

## Runtime validation

The Mira-controlled runtime should reject or quarantine provider output that cannot be normalized into this contract.

A provider's native approval state, score, prose summary, emoji reaction, or severity naming is not authoritative unless the runtime maps it into the normalized Mira contract.

## Stale result

The publisher / consumer must treat a review as stale when its recorded review identity no longer matches the current PR head or the trusted controls used for the current review.

A stale review may remain visible as history, but must not be presented as the current review result.
