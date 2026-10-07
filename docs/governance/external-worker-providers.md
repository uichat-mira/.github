# External Worker provider and model contract

Status: active Organization guidance.

The Mira External Worker supports a small run-scoped provider/model contract. Provider selection is execution input, not a persistent repository, user, or machine-wide OpenCode setting.

## Backward compatibility

Existing callers remain valid.

If a caller supplies no new provider inputs, the Worker keeps the proven route:

- provider: `opencode-go`
- model: `deepseek-v4.1-flash`
- credential: legacy `opencode_go_api_key` secret

The compatibility path feeds the same internal provider-resolution and OpenCode invocation path as new callers; it is not a second routing implementation.

## Dispatch inputs

Optional reusable-workflow inputs:

| Input | Meaning |
| --- | --- |
| `provider` | OpenCode provider identifier. Defaults to `opencode-go`. |
| `model` | Provider-local model identifier. Defaults to `deepseek-v4.1-flash`. |
| `provider_profile` | Optional trusted profile declared in the Organization provider registry. |
| `provider_registry_ref` | Required with a profile. Must be an immutable 40-character commit SHA of `uichat-mira/.github`. |

Optional secrets:

| Secret | Meaning |
| --- | --- |
| `opencode_go_api_key` | Backward-compatible credential for the default OpenCode Go route. |
| `provider_api_key` | Run-scoped credential for the explicitly selected provider. |

Credentials never belong in the registry.

A custom route supplies a provider matching the profile's `provider_id`, for example:

```yaml
jobs:
  worker:
    uses: uichat-mira/.github/.github/workflows/mira-external-worker.yml@<frozen-ref>
    with:
      issue_number: 123
      base_branch: main
      verification_command: npm test
      provider: mira-openrouter
      model: deepseek/deepseek-chat-v3.1
      provider_profile: openrouter
      provider_registry_ref: <40-character commit sha>
    secrets:
      provider_api_key: ${{ secrets.OPENROUTER_API_KEY }}
```

## Frozen provider registry

Custom provider metadata lives in [`.github/mira-external-worker-providers.json`](../../.github/mira-external-worker-providers.json).

A profiled run must pass the exact commit SHA containing the registry. The Worker refuses a floating branch or tag. The resolved commit SHA is checked against the requested SHA and recorded in run evidence.

This keeps provider metadata frozen with the execution contract instead of silently following `main`.

The registry may contain only non-secret OpenCode provider metadata needed by a route, such as:

- adapter/npm package;
- display name;
- HTTPS endpoint/base URL;
- model declaration/mapping;
- bounded non-secret provider options.

It is not a general model gateway, automatic router, retry/fallback chain, or credential store.

## Fail-closed rules

Before model execution the Worker rejects:

- malformed provider/model/profile identifiers;
- a custom provider without a profile;
- a profile without an immutable registry commit SHA;
- an unknown profile;
- a provider that does not match the profile;
- a model not declared by the profile;
- an invalid provider adapter or non-HTTPS custom base URL;
- a missing credential for the effective provider.

These failures occur before implementation commit or Draft PR creation.

## Run-scoped OpenCode configuration

The effective route is applied only through process-scoped OpenCode surfaces:

- `OPENCODE_AUTH_CONTENT`;
- `OPENCODE_CONFIG_CONTENT`;
- `opencode run --model <provider/model>`.

The Worker does not mutate repository `opencode.json`, `~/.config/opencode`, persistent OpenCode auth state, or unrelated Agent defaults.

## Evidence

The structured Worker evidence package records:

- provider;
- provider profile;
- frozen provider registry ref and resolved SHA;
- model;
- effective model route;
- provider-resolution stage outcome.

Provider credentials and raw environment values are excluded from persisted evidence.
