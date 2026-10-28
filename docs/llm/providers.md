# Provider resolution

`home/.chezmoidata/llm/common.yaml` owns endpoints, credential references and
shared provider definitions. Tool files in the same directory declare only
their additions, overrides and model candidates. Read those files for current
values; generated agent configs are not the source of truth.

## Defaults and overrides

`llm/tool-config` resolves provider references in this order:

1. `llm.default_providers` (omitted or empty means no defaults).
2. The tool's `provider_sets`, in list order.
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
- The client's `supported_provider_types`. A gateway's `api_types` can supply a
  compatible protocol when its default is unsupported. An explicit reference
  `type` is never silently changed.
- Per-tool provider policy, including the OpenRouter exclusion on Pi, OMP,
  Hermes and OpenCode. Defaults and sets cannot bypass it.

Unknown provider or set references fail rendering. Disabled, incompatible or
excluded aliases do not contribute picker patterns; explicit patterns naming
those aliases are removed too.

Provider registration does not choose a default model. Model candidate lists
select the first resolved alias as described in [model selection](model-roles.md).
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

## Validation

Run `make verify` after changing provider data or renderers. Offline tests in
`scripts/test-llm-providers.py` and `scripts/test-llm-client-providers.py` cover
inheritance, exclusions, protocol negotiation, model routing, native rendering,
write failure/retry and cleanup. They do not invoke real auth helpers or gateways.

Native contracts: [Aider model settings](https://aider.chat/docs/config/adv-model-settings.html),
[Goose custom providers](https://github.com/aaif-goose/goose/blob/main/documentation/docs/getting-started/providers.md),
[Goose auth.command schema](https://github.com/aaif-goose/goose/blob/main/crates/goose-providers/src/declarative.rs),
[CC gateway protocol](https://code.claude.com/docs/en/llm-gateway-protocol),
[Magpie gateway protocols](https://github.com/yetone/magpie/blob/v0.1.1477/docs/integrating.md).
