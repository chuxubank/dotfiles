# Shared provider defaults

`home/.chezmoidata/llm/common.yaml` owns endpoints, credentials and shared
provider references. Agent files in the same directory only need to declare
additions or differences.

## Defaults and overrides

A default provider list is inherited by every `llm.tools` entry:

```yaml
llm:
  default_providers: [magpie]
```

The map form supports aliases and shared options, just like a tool's
`providers` map:

```yaml
llm:
  default_providers:
    gateway:
      provider: magpie
      type: openai
  tools:
    pi:
      providers:
        gateway:
          models: false
    example-client:
      exclude_providers: [gateway]
```

`llm/tool-config` resolves references in this order:

1. `llm.default_providers` (omitted or empty means no defaults).
2. The tool's `provider_sets`, in list order.
3. The tool's `providers` entries.
4. The tool's `exclude_providers`, which removes aliases even if a set or
   explicit tool entry declared them.

Map entries are deep-merged: a tool can override one field without copying
`provider`, auth settings or nested options. Short-form tool entries use the
name as both alias and provider, retaining other inherited settings. Exclusions
name the **alias**, not the underlying provider. An empty tool `providers` list
does not opt out of defaults; use `exclude_providers` instead.

The resulting references still follow provider host conditions and `owner`
tool switches. Clients may declare `supported_provider_types`; incompatible
protocols are filtered rather than excluding a provider by name. A gateway
can advertise `api_types` (Magpie: OpenAI, Anthropic, Gemini). If its default
protocol is unsupported, the resolver uses the first advertised protocol the
client supports. An explicit reference-level `type` is never silently changed.
Disabled, incompatible or excluded aliases do not contribute provider picker
globs. Excluded aliases' explicit picker patterns are removed as well.
Defaults only register selectable providers: they do not change `model`,
`small_model` or OMP role assignments. Candidate lists continue selecting the
first available alias.

Unknown provider/set references fail rendering. Pi, OMP, Hermes and OpenCode
reject OpenRouter in the effective references, including references inherited
from defaults or sets; defaults must not bypass the per-tool policy.

## Current Magpie wiring

`default_providers: [magpie]` replaces the identical declarations formerly
repeated in Codex, Pi, OMP, OpenCode, Hermes and craft-agents. Aider, Goose
and Claude Code inherit it too; none excludes it by name. Grok Build and
Cursor CLI do not consume `llm/tool-config` and are unaffected.

The `magpie` entry in `home/.chezmoidata/tools.yaml` is a client switch, enabled
on non-CI hosts. It does not install or start Magpie. Disabling it removes the
inherited alias. Existing default models and OMP roles remain unchanged.

The gateway origin is built from the provider definition in `common.yaml`:

- Scheme: `public_scheme` (`https`).
- Subdomain: `public_prefix` (`magpie`).
- Domain: the `domain` field of pass entry
  `Network/Host/BandwagonHost/CN2/ssh`.
- Gateway credential: the `gateway-key` field of pass entry
  `Personal/Tech/AI/Magpie`.

This produces `https://magpie.<domain>`. A literal `base_url` on the provider
wins over this construction. OpenAI-compatible API bases append `/v1` through
`llm/model-endpoint`. The model list is fetched from `/v1/models` and cached at
`~/.cache/llm/models/magpie.json`. Pi, OMP and Codex use `pass-field` to retrieve
the key; OpenCode and Hermes receive the resolved credential in their config.
Upstream provider keys and the VPS gateway deployment are not managed here.

## Aider, Goose and Claude Code

Inheriting a provider makes it available; it does **not** choose a default
model or enable a disabled tool.

- **Aider** supports OpenAI, Anthropic, Gemini and Ollama. The private
  `~/.aider.model.settings.yml` enumerates provider models using
  `<alias>/<upstream-id>` names. Each model's LiteLLM `extra_params` carries
  its own API base, credential, protocol and original upstream id, so multiple
  gateways do not compete over one global `OPENAI_API_BASE`. For a Magpie id
  `vendor/model`, use `magpie/vendor/model`. The file contains resolved keys
  and is mode `0600`.
- **Goose** supports OpenAI, Anthropic and Ollama. A dedicated `run_onchange`
  script writes one native JSON definition per custom alias under
  `~/.config/goose/custom_providers/custom_chezmoi_<alias>.json`. It uses
  Goose's `auth.command` with `pass-field` and dynamic model discovery.
  Only that reserved prefix is pruned when aliases disappear or Goose is
  disabled; native definitions and user files are untouched. Select a model
  in `llm.tools.goose.model` as `magpie/vendor/model`; the renderer maps the
  provider to `custom_chezmoi_magpie` and keeps `vendor/model` as the model id.
  The existing OpenRouter default remains explicit and unchanged.
- **Claude Code** speaks Anthropic Messages and has **one active endpoint**,
  not a provider registry. Magpie negotiates its Anthropic surface, while a
  genuinely OpenAI-only provider is filtered. Set
  `llm.tools.claude-code.model: magpie/vendor/model` to select that endpoint;
  CC receives `vendor/model` and the gateway origin without `/v1`. If the
  model has no provider alias, the existing `anthropic` alias wins, otherwise
  native login stays in control. Inheriting Magpie alone never reroutes CC by
  map iteration order. When using `opusplan` or tier aliases, configure the
  tier model ids in `default_models` for the chosen endpoint as well.

Offline tests in `scripts/test-llm-providers.py` and
`scripts/test-llm-client-providers.py` cover inheritance, protocol negotiation,
model routing, native rendering, Goose write failure/retry, cleanup and CC
endpoint selection. No agent, real auth helper or gateway is invoked.

Native contracts: [Aider model settings](https://aider.chat/docs/config/adv-model-settings.html),
[Goose custom providers](https://github.com/aaif-goose/goose/blob/main/documentation/docs/getting-started/providers.md),
[Goose auth.command schema](https://github.com/aaif-goose/goose/blob/main/crates/goose-providers/src/declarative.rs),
[CC gateway protocol](https://code.claude.com/docs/en/llm-gateway-protocol),
[Magpie gateway protocols](https://github.com/yetone/magpie/blob/v0.1.1477/docs/integrating.md).
