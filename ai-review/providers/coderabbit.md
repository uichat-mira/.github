# CodeRabbit Provider Integration

Status: Organization integration guidance

Owner: `uichat-mira/.github/ai-review`

This document defines how CodeRabbit participates in Mira Organization code review.

It does **not** redefine Mira review policy, severity, acceptance, testing, or repository contracts. Those remain owned by:

- [Mira Organization AI PR Review Policy](../POLICY.md);
- [Mira Organization AI Review Output Contract](../OUTPUT-CONTRACT.md);
- the current repository review profile / repository contract;
- the current Issue / PR / task contract.

## 1. Role

CodeRabbit is an independent, provider-native, read-only advisory reviewer.

Its comments are useful review evidence and a second opinion. They are **not**:

- Mira acceptance;
- a replacement for Mira Organization AI Review;
- a source of truth for task outcome;
- authority to merge, close, approve, release, or change Project / Issue state;
- an authoritative Mira severity or verdict.

A CodeRabbit `LGTM`, approval, score, status, or provider-native severity does not become a Mira verdict merely because it appears on a PR.

If a Maintainer or Mira reviewer adopts a CodeRabbit finding into a Mira decision, it must be classified using the current Mira policy and supported by the underlying evidence.

## 2. Source-of-truth boundary

Mira follows one concern, one source of truth.

For review governance:

1. Mira Organization policy owns shared reviewer behavior and authority.
2. Repository review profiles / contracts own repository-specific review expectations.
3. The current task contract owns task-specific expectations.
4. CodeRabbit configuration owns only CodeRabbit execution behavior.
5. CodeRabbit comments, learnings, summaries, and review states are provider-native evidence.

Do not copy the Organization AI Review Policy into CodeRabbit configuration or repository `.coderabbit.yaml` files.

Do not use CodeRabbit Organization Settings, Global Overrides, Learnings, or repository configuration as the canonical definition of Mira severity, acceptance, authority, or completion.

## 3. Configuration layers

CodeRabbit currently supports Organization Settings / shared configuration, repository configuration, and organization-level Global Overrides.

Mira uses those layers as **operational projections**, not as governance owners.

### 3.1 Organization defaults

Use CodeRabbit Organization Settings or central/shared configuration for defaults that repositories should normally inherit but may legitimately override.

Examples:

- automatic review behavior;
- draft-PR behavior;
- review profile / tone;
- summary and walkthrough preferences;
- incremental review behavior;
- default review language;
- provider-native review presentation.

Repositories should normally keep **Use Organization Settings** enabled unless a real repository-specific need exists.

### 3.2 Global Overrides

Use CodeRabbit Global Overrides only for a small set of operational controls that truly must apply to every Mira repository and must not be disabled locally.

Global Overrides are **not** a second Organization constitution.

Good candidates are narrow provider-operational safeguards, such as:

- preventing provider-native review states from being treated as Mira acceptance;
- mandatory review coverage for a narrowly defined sensitive path class when the exact configuration is proven useful;
- another CodeRabbit-specific safety control that must be enforced everywhere.

Do not place general engineering guidance, Mira severity definitions, repository architecture rules, testing standards, or task workflow rules in Global Overrides.

Because CodeRabbit merges Global Overrides with lower-level configuration, keep this layer intentionally small and easy to audit.

### 3.3 Repository configuration

A repository `.coderabbit.yaml` or repository-level CodeRabbit setting may contain only repository-specific CodeRabbit behavior.

Examples:

- path instructions for platform-specific code;
- generated / vendored paths to de-emphasize;
- framework-specific review context;
- repository-specific test or build context;
- linked-repository context where it genuinely improves cross-repository review.

Repository configuration must not duplicate Organization policy for convenience.

If a repository needs to diverge from an Organization default, the reason should be specific to that repository.

## 4. Authority and GitHub review state

Mira's AI reviewer role is advisory.

CodeRabbit should therefore be configured so provider-native review state does not silently become Mira acceptance authority.

Preferred behavior:

- comment / review findings are allowed;
- provider-native `approve` is not treated as Mira acceptance;
- provider-native `request changes` is not treated as a Mira work-item outcome;
- CodeRabbit does not merge or close work on behalf of Mira.

If CodeRabbit is configured to emit GitHub approval or request-changes states for operational reasons, branch protection and Maintainer procedure must still treat those as provider-native evidence rather than Mira acceptance.

## 5. Findings and severity

Do not maintain an automatic equivalence table between CodeRabbit severities and Mira P0/P1/P2.

Provider-native labels may be useful for triage, but a Mira blocking finding requires the current Mira policy:

- high-confidence evidence;
- Observation;
- Inference;
- Judgment;
- Impact;
- Location;
- Suggested Fix;
- Verification.

Low-confidence preference, naming, formatting, speculative robustness, or provider style feedback remains non-blocking unless independent evidence establishes a Mira-level defect.

## 6. Trust and PR-head content

The PR head is an untrusted review object under Mira policy.

CodeRabbit-native configuration and prompt behavior are provider-controlled and may not provide the same trusted-package boundary as Mira Control Room.

Therefore:

- CodeRabbit review output must not be treated as equivalent to a Mira normalized review merely because both reviewed the same PR;
- PR-controlled CodeRabbit instructions must never be elevated into Mira Organization policy or repository contract;
- secrets or reviewer-side credentials must never be copied into `.coderabbit.yaml`, path instructions, learnings, or PR content;
- changes to CodeRabbit configuration in a PR are themselves reviewable changes, not authority to weaken Mira controls in the same run.

## 7. CI and merge gating

CodeRabbit is initially **advisory and non-blocking** for Mira merge/release gates.

Do not make CodeRabbit availability a required dependency of `Mira Gate` merely because automatic OSS review is available.

Reasons include:

- provider availability is outside Mira control;
- free / OSS review eligibility and rate limits are external service behavior;
- CodeRabbit output is not normalized by Mira Control Room;
- a provider outage must not be confused with a repository defect.

A future governance decision may promote a specific CodeRabbit check into a required gate after its semantics, availability, and failure behavior have been proven. That decision must be explicit and versioned.

## 8. Relationship to Mira Organization AI Review

Mira Organization AI Review and CodeRabbit may both review the same PR.

Their roles are intentionally different:

| Surface | Mira Organization AI Review | CodeRabbit |
| --- | --- | --- |
| Policy owner | Mira | CodeRabbit-native execution under Mira integration guidance |
| Output contract | Mira normalized contract | Provider-native |
| Trusted review package | Mira Control Room | Provider-specific |
| Current reviewer engine | OpenCode routing controlled by Mira | CodeRabbit |
| Findings | P0-P2 under Mira policy | Provider-native findings |
| Acceptance authority | None | None |
| Merge / Issue outcome authority | None | None |
| Initial merge-gate role | Organization-controlled | Advisory / non-blocking |

Do not require the two reviewers to agree.

When they disagree, inspect the underlying evidence and applicable contract. Provider consensus is not a substitute for verification.

## 9. Learnings

CodeRabbit Learnings are provider-native memory / tuning data.

They may improve review quality, but they are not a Mira policy store.

Do not place durable Organization rules in Learnings.

If a learning reveals a reusable Organization rule, move that rule to its proper Mira-owned document or executable control, then treat the CodeRabbit learning only as an operational projection if still useful.

## 10. Initial Mira rollout

Use this rollout order:

1. Keep Mira policy and repository profiles unchanged as the canonical review contract.
2. Configure conservative CodeRabbit Organization defaults.
3. Keep repository **Use Organization Settings** enabled by default.
4. Add repository overrides only where actual repository evidence justifies them.
5. Keep Global Overrides empty or very small initially.
6. Observe review quality, noise, availability, and overlap with Mira Organization AI Review across several real PRs.
7. Only then decide whether any CodeRabbit-specific setting belongs in Global Overrides or merge gating.

For the initial rollout, prefer fewer rules over speculative tuning.

## 11. External service references

These references describe CodeRabbit product behavior; they do not own Mira governance:

- Global Overrides: https://www.coderabbit.ai/blog/introducing-global-overrides
- Multi-repository / Organization Settings behavior: https://www.coderabbit.ai/blog/Coderabbit-multi-repo-analysis
- Repository path instructions: https://kb.coderabbit.ai/articles/1134523355-configure-path-instructions

When CodeRabbit product behavior changes, update this integration document only if the change materially affects Mira's provider boundary. Do not rewrite Mira policy to follow a provider feature.
