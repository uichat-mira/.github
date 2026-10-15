# External Worker provider and model selection

Status: active Organization guidance.

The Mira External Worker (reusable workflow `mira-external-worker.yml`) can be dispatched with a run-scoped OpenCode provider and model. Provider/model choice is a dispatch-time execution input for one run; it is not a property of the Worker role and does not couple the Worker to any single vendor.

Every route keeps the same Worker execution role, permission boundary, Skill, trusted verification, Git mutation, and Draft PR rules.

## Run-scoped contract

The reusable workflow accepts:

| Input | Meaning |
| --- | --- |
| `provider` | OpenCode provider identifier for this run. Defaults to `mira-opencode-console` (free DeepSeek Console route). |
| `model` | Model identifier for this run. Defaults to `deepseek-v4.1-flash-free`. |
| `provider_profile` | Optional profile name from the frozen Organization provider registry. |
| `provider_registry_ref` | Immutable 40-character `.github` commit SHA that contains the registry. Required when `provider_profile` is set. |

Credentials are passed only through declared caller-owned secrets:

| Secret | Meaning |
| --- | --- |
| `opencode_go_api_key` | Backward-compatible credential for the built-in `opencode-go` route. |
| `provider_api_key` | Run-scoped credential for the selected provider. |

## Default free route and backward compatibility

Without explicit route inputs, the Worker chooses `mira-opencode-console/deepseek-v4.1-flash-free` and resolves the `opencode-console-free` profile from the frozen Organization registry commit `aa844024cb9de98b00f485ffd0daa15b7057ae99`. This is a **limited-time** free Console model, not a permanent entitlement. New deployments must not silently fall back to a paid model if its authentication or availability fails.

Maintainers can still select the existing paid Go route for an individual run by passing `provider=opencode-go`, `model=deepseek-v4.1-flash`, and no profile. An explicit custom `provider_profile` and immutable registry ref continue to override the default profile selection. Both routes retain the same workflow, governed execution, verification, and Draft PR boundaries. For the default Console route the Worker uses `provider_api_key` first, or the legacy `opencode_go_api_key` if that is all a caller passes; a Go credential may not grant Console entitlement, so a live authenticated check remains required. Credential failure terminates the run before commit/PR creation. No automatic paid-model fallback is provided.

## Frozen provider registry

Profile metadata is read from the Organization registry at `.github/mira-external-worker-providers.json` in `uichat-mira/.github`, resolved at the caller-supplied immutable `provider_registry_ref`, never from a floating branch. A profile requested without a valid immutable registry ref fails the run.

Registry shape:

```json
{
  "schema_version": 1,
  "profiles": {
    "<profile>": {
      "provider_id": "<opencode-provider-id>",
      "config": {
        "npm": "<opencode provider adapter package>",
        "name": "<display name>",
        "options": { "baseURL": "https://..." },
        "models": { "<model-id>": { "name": "<display name>" } }
      }
    }
  }
}
```

Each profile declares a `provider_id` that must match the requested `provider`, and an OpenCode provider `config` with:

- `npm` — the supported OpenCode provider adapter/package;
- `options` — provider options such as the endpoint base URL;
- `models` — the model identifiers that profile is allowed to run.

The registry is a small, trusted Organization configuration surface for endpoint/adapter metadata. It must not carry credentials, and it must not grow into a model gateway, auto-router, fallback chain, or general-purpose orchestration platform.

### Validated custom-provider example

The `volcengine-coding-plan` registry profile is a concrete, validated custom-provider route executed through the same reusable Worker contract:

| Field | Value |
| --- | --- |
| `provider_profile` | `volcengine-coding-plan` |
| `provider` | `volcengine-plan` |
| `model` | `deepseek-v4.1-flash` |
| Credential | `provider_api_key` (trusted caller secret) |

The run supplied `provider_profile`, `provider`, `model`, and a matching immutable `provider_registry_ref`, and resolved the profile config from the frozen registry at that revision (`1829a72d16a60d65f5982ff77c41140ec4d9261f` at the time of validation). Endpoint, adapter, and model metadata remain owned by the registry entry; this section records only the reusable route identity, not a second copy of the provider config.

## OpenCode Console free DeepSeek Worker route

The `opencode-console-free` frozen registry profile provides `mira-opencode-console/deepseek-v4.1-flash-free` for dispatches that explicitly select it. It targets OpenCode Console's `https://opencode.ai/inference/v1/chat/completions` endpoint using the `@ai-sdk/openai-compatible` adapter. The model's published default context is 200K. **This is not the paid `opencode-go/deepseek-v4.1-flash` route.**

The Console free model is a limited-time offering. Its availability, rate limits, and credentials can change; a failed Console call must be reported as failure, never silently rerouted to a paid model. The caller supplies the key through the existing `provider_api_key` secret channel, using an independent Console credential when available. A Go key should not be assumed to grant Console access without a real authenticated smoke test.

The provider profile and its immutable registry SHA are owned by this repository. Product-repository callers may select the profile for their own Worker runs; unrelated OpenCode sessions and explicitly chosen run-scoped models are unchanged.

## Isolation

Selection is run-scoped and process-local:

- credentials and provider config are supplied through `OPENCODE_AUTH_CONTENT` and `OPENCODE_CONFIG_CONTENT` for the Worker process only;
- the Worker must not require or perform persistent mutation of a maintainer's local OpenCode configuration, `~/.config/opencode`, a repository `opencode.json`, or defaults used by unrelated agents, jobs, or sessions.

## Credentials

Provider keys come only from trusted GitHub Secrets or equivalent trusted caller-owned secret inputs. They must not be committed to the registry or repository files, persisted in artifacts, or included in logs or Draft PR handoff text.

## Evidence

Each run records the requested and effective provider, provider profile, model, and model route and, when a profile is used, the frozen registry revision and resolved registry SHA. See [`external-worker-evidence.md`](external-worker-evidence.md).

## Failure behavior

An invalid provider identifier, an unknown profile, a mismatched provider/profile, an unknown or disallowed model, an invalid registry config, or a missing immutable registry ref fails the run before the model executes, so no implementation commit or Draft PR is produced. Provider capability differences surface as explicit failures rather than silent normalization or downgrade.

## Non-goals

No custom provider proxy or gateway, no automatic best-model router, no billing/price optimization, no multi-model debate, fallback chain, or retry policy, and no changes to unrelated OpenCode agent configuration.
