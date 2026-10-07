# External Worker provider and model selection

Status: active Organization guidance.

The Mira External Worker is an execution role, not a vendor binding. This document defines how one Worker run selects its OpenCode provider profile and model while the Worker contract, authority, Skill, verification, Git flow, and evidence model stay unchanged.

Exact input, secret, and file identifiers are owned by the reusable Worker workflow and its provider registry/profile. Those executable surfaces are authoritative for current technical reality; this document owns the Organization-level contract they must satisfy.

## 1. Run-scoped selection

Provider/profile and model selection is a dispatch-time execution input owned by the trusted caller. It is not a fixed property of the Worker role and not a property of Organization OpenCode configuration.

A trusted caller selects a provider profile (or provider identifier) and a model for a single run. The selection applies only to that run.

Selecting a different provider or model must not change:

- Worker authorization and permission boundaries;
- the Issue / Skill / trusted-verification contract;
- Git mutation, Draft PR, or evidence semantics;
- merge, Issue outcome, release, deployment, or promotion authority.

## 2. Configuration isolation

The Worker injects the selected provider's auth and configuration into the Worker process only, using supported OpenCode run-scoped mechanisms such as environment-provided auth and config content.

A run must not require or perform persistent mutation of:

- a maintainer's local OpenCode configuration;
- `~/.config/opencode` or persistent auth state;
- repository `opencode.json` or equivalent shared Agent config merely to select a Worker provider;
- defaults used by unrelated Agents, jobs, or developer sessions.

## 3. Backward compatibility

Existing authorized callers that supply only the established `opencode-go` credential and do not select a provider/profile/model continue to run on the pinned default route `opencode-go/deepseek-v4.1-flash`.

Compatibility is an input default on one canonical execution path. It is not a second routing system, gateway, fallback chain, or retry policy.

## 4. Provider registry / profile

Where a provider needs endpoint/base URL, adapter/package, headers/options, or model mapping, that metadata lives in a small trusted Organization/Worker configuration surface: the provider registry/profile.

- The registry/profile may describe provider connection metadata and model mapping.
- Provider credentials never live in the registry/profile. They are supplied only through trusted caller-owned GitHub Secrets or equivalent trusted secret inputs.
- The registry/profile must not become a general-purpose model gateway, orchestration platform, or automatic router.
- Provider capability differences (tool calling, reasoning options, headers, compatibility layers) fail explicitly rather than being silently normalized or downgraded.

## 5. Frozen revision

The provider registry/profile source used by a run is tied to the same immutable Worker revision, or to an explicitly frozen revision supplied by trusted caller input.

A run must not resolve provider metadata from a floating `main` while executing an immutable Worker revision. Execution identity therefore does not silently drift, and the evidence package records the effective provider/profile/model and the frozen registry/config revision when one applies.

## 6. Fail closed

An unknown or invalid provider profile/model, or a missing required credential, fails the run before it produces an implementation commit or Draft PR. The Worker does not silently fall back to another route.

## 7. Evidence

The #39 structured Worker evidence package records the requested and effective provider/profile and model route for the run. See [`external-worker-evidence.md`](external-worker-evidence.md).

## 8. Non-goals

This contract does not introduce:

- a custom provider proxy or gateway;
- an automatic "best model" router;
- a billing/price optimization engine;
- a multi-model debate, fallback chain, or retry policy;
- changes to unrelated OpenCode Agent configuration;
- exposure of every OpenCode provider option as a dispatch input.
