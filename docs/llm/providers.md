# Provider resolution

`home/.chezmoidata/llm/common.yaml` owns endpoints, credential references and
shared provider definitions. Tool files in the same directory declare only
their additions, overrides and model candidates. Read those files for current
values; generated agent configs are not the source of truth.

## Defaults and overrides

`llm/tool-config` resolves provider references in this order:

1. `llm.default_providers` (omitted or empty means no defaults).
2. `llm.default_provider_sets`, then the tool's `provider_sets`, in list order.
3. The tool's `providers` entries.
4. The tool's `exclude_providers`.

Defaults and tool references accept a list of provider names or an alias map.
List entries use the name as both alias and provider. Map entries can rename
a provider and override its options; nested options are deep-merged rather
than replacing the whole reference.

Exclusions name the **alias**, not the underlying provider, and win over all
other declarations. An empty tool `providers` list does not opt out of defaults.
Use `exclude_providers` for that.

The merged references then pass through:

- Provider host conditions and the `owner` tool switch.
- The client's `supported_provider_types`. A provider has no `type`: the
  primary protocol is its first `api_types` entry, otherwise
  `openai-completions`. Later entries supply a compatible protocol when the
  client rejects the primary. An alias `type` pins the protocol and is never
  silently changed. Protocol ids are Pi's `KnownApi` names
  (`openai-completions`, `openai-responses`, `anthropic-messages`,
  `google-generative-ai`). `ollama` and `opencode` only select the model-list
  fetch. Adapters translate those ids into the client's own field.
- Per-tool provider policy, including the OpenRouter exclusion on Pi, OMP,
  Hermes and OpenCode. Defaults and sets cannot bypass it.

Shared provider sets apply to every configured client; adding a client must not
require copying the IV alias table. Host conditions and protocol compatibility
still gate each alias. Clients with a picker allowlist inherit the provider's
patterns, so registering a provider cannot leave its catalog unselectable.

Unknown provider or set references fail rendering. Disabled, incompatible or
excluded aliases do not contribute picker patterns; explicit patterns naming
those aliases are removed too.

Provider registration does not choose a default model. Model candidate lists
select the first resolved alias. A launch wrapper can replace that result;
the full order is in [model selection](model-roles.md).
`models: false` preserves the client's catalog; it does not disable the provider
or suppress credential injection.

## Gateway lifecycle

The Magpie entry in `home/.chezmoidata/tools.yaml` controls client registration,
not gateway installation or startup. The provider's `owner` follows that switch;
when disabled, its inherited alias disappears from resolved client config.
Upstream accounts and gateway deployment remain outside this repository.

Endpoint and credential construction belong to the provider definition:

- A literal `base_url` wins over an origin built from `public_scheme`,
  `public_prefix` and the `public_domain` credential reference.
- `llm/model-endpoint` adds the protocol-specific API path.
- `model_caches` and `home/.chezmoidata/path.toml` own model-discovery caches.
  Pi/OMP preserve the endpoint's exact ids, limits, input modalities, reasoning
  levels and prices. Discovery normalizes these into the shared model format;
  endpoint metadata overrides vendor catalog data, then explicit per-model
  overrides win. Missing fields keep the renderer's fallbacks. Advertised
  per-token prices are converted to the clients' per-million-token unit.
- Clients with a command-based credential field use `pass-field`; other
  clients receive the resolved key in their private config.

Do not use Magpie's agent-config writer against files chezmoi manages. The
repo owns client rendering; Magpie serves requests behind the configured endpoint.

## Client adapters

- **Aider** enumerates `<alias>/<upstream-id>` models in its private model
  settings. Each entry carries its own protocol, endpoint, credential and
  upstream id, so multiple gateways do not compete over global environment
  variables.
- **Goose** gets one native custom-provider definition per alias. A dedicated
  `run_onchange` transaction writes and prunes only the reserved
  `custom_chezmoi_` namespace, leaving native and user definitions alone. The
  renderer translates the selected alias into that namespace and preserves the
  upstream model id. Authentication uses a command and discovery is dynamic.
- **Claude Code** has one active endpoint rather than a provider registry. An
  explicitly qualified model selects the provider; without one, the configured
  Anthropic alias or native login remains in control. Inheritance alone must
  not select an endpoint by map iteration order. Tier-model assignments must
  belong to the chosen endpoint too.
- **Copilot** has one BYOK endpoint per launch, not a provider registry.
  `llm/copilot.yaml` selects it the same way as other tools. The `~/bin/copilot`
  wrapper exports `COPILOT_PROVIDER_BASE_URL`, `COPILOT_PROVIDER_TYPE`,
  `COPILOT_PROVIDER_WIRE_API`, and `COPILOT_PROVIDER_API_KEY_COMMAND`
  (`pass-field` with the alias's auth path). `COPILOT_MODEL` and `--model`
  are the upstream id. The key is not written into the script. Directory
  rules use the same qualified reference as the other clients.
- **Grok Build** enumerates each compatible provider into local
  `model.<alias/upstream-id>` rows. `model_providers.<alias>` owns the endpoint
  and backend; named `auth_provider.<alias>` helpers call `pass-field` without
  changing native session auth. Discovery metadata supplies context and output
  limits. The default and directory launches use the same qualified catalog
  keys as Pi and OMP. Do not combine this with a global authenticated models
  endpoint: that mode ignores the local model tables. Rendering removes the
  former global endpoint and stale managed rows while preserving user entries.

## Validation

Run `make verify` after changing provider data or renderers. Offline tests in
`scripts/test-llm-providers.py` and `scripts/test-llm-client-providers.py` cover
inheritance, exclusions, protocol negotiation, model routing, native rendering,
write failure/retry and cleanup. They do not invoke real auth helpers or gateways.

Native contracts: [Aider model settings](https://aider.chat/docs/config/adv-model-settings.html),
[Goose custom providers](https://github.com/aaif-goose/goose/blob/main/documentation/docs/getting-started/providers.md),
[Goose auth.command schema](https://github.com/aaif-goose/goose/blob/main/crates/goose-providers/src/declarative.rs),
[CC gateway protocol](https://code.claude.com/docs/en/llm-gateway-protocol),
[Magpie gateway protocols](https://github.com/yetone/magpie/blob/v0.1.1477/docs/integrating.md),
[Grok custom models](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/11-custom-models.md),
[Grok per-model auth](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-shell/README.md#per-model-auth-providers).
