# External Worker provider and model selection

Status: active Organization guidance.

The Mira External Worker (reusable workflow `mira-external-worker.yml`) can be dispatched with a run-scoped OpenCode provider and model. Provider/model choice is a dispatch-time execution input for one run; it is not a property of the Worker role and does not couple the Worker to any single vendor.

Every route keeps the same Worker execution role, permission boundary, Skill, trusted verification, Git mutation, and Draft PR rules.

## Run-scoped contract

The reusable workflow accepts:

| Input | Meaning |
| --- | --- |
| `provider` | OpenCode provider identifier for this run. Defaults to the built-in `opencode-go` route. |
| `model` | Model identifier for this run. Defaults to `deepseek-v4.1-flash` on the built-in route. |
| `provider_profile` | Optional profile name from the frozen Organization provider registry. |
| `provider_registry_ref` | Immutable 40-character `.github` commit SHA that contains the registry. Required when `provider_profile` is set. |

Credentials are passed only through declared caller-owned secrets:

| Secret | Meaning |
| --- | --- |
| `opencode_go_api_key` | Backward-compatible credential for the built-in `opencode-go` route. |
| `provider_api_key` | Run-scoped credential for the selected provider. |

## Built-in route and backward compatibility

With no `provider_profile`, the run uses the built-in `opencode-go` route and the `opencode_go_api_key` secret. This keeps existing authorized callers working without coordinated migration.

Built-in and profile routes are not two routing systems. Both resolve through the same credential, config, and `opencode run --model <provider>/<model>` path; only the credential source and provider config differ. When `provider_api_key` is supplied it takes precedence, otherwise the built-in route falls back to `opencode_go_api_key`.

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
