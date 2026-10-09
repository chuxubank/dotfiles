# Data validation boundaries

`make verify` validates source YAML/TOML against JSON Schema before running
resolver templates. Schema checks do not fetch model catalogs or credentials.

| Schema | Source | Contract |
| --- | --- | --- |
| `tools.schema.json` | `tools.yaml` | switches, cleanup paths/commands, plugin-upgrade argv, RTK cleanup policy |
| `packages.schema.json` | `packages/**/*.toml` | string/map packages, `owner` (not `tool`), package option types |
| `skills.schema.json` | `skills/*.yaml` | agents, external skills, provider groups, owners and conditions |
| `defaults.schema.json` | `defaults.yaml` | domains, keys, owners, gated values |
| `plugins.schema.json` | `plugins/*.yaml` | providers/marketplaces, Pi npm trust, mitsupi resource filters |
| `llm-policy.schema.json` | `llm/*.yaml` | no OpenRouter provider on Pi, OMP, Hermes or OpenCode |
| `integrations.schema.json` | `integrations.yaml` | integration declaration structure |
| `plugin-managers.schema.json` | `plugin-managers.yaml` | plugin lifecycle manager structure |

`llm-policy` is intentionally a policy overlay, not a schema for all model
metadata. It allows unrelated catalog fields and providers. Package options
share one declaration shape across ecosystems; this does not prove a particular
package manager accepts every option.

YAML files with full schemas carry a `yaml-language-server` schema comment.
Schemas reuse the shared host-condition definitions; skill/plugin conditions
also accept `tool` because it identifies the target agent, not the owner.

Keep the following outside static schema checks:

- Cross-file references: an `owner` must name a declared tool; integration
  targets must exist and their paths must stay inside the agent root.
- Relationships between values: command cleanup and string cleanup must not
  overlap; workspace panes must resolve to one root.
- Resolver and rendering behavior: host filtering, provider resolution, exact
  ignore scope, model overlays, and platform path conversion.
- Execution behavior: failure propagation, partial cleanup detection, retry,
  literal argument handling and idempotence. Test with offline stubs only.

`verify/model` owns merged-data semantic checks; `verify/contracts` tests
resolver behavior with fixtures. Neither repeats field/type validation already
owned by a schema. The integration semantic checker remains authoritative for
its cross-file references and path containment.
