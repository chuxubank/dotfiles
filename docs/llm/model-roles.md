# Model selection and OMP roles

## Sources of truth

- `home/.chezmoidata/llm/common.yaml`: shared model aliases and provider definitions.
- `home/.chezmoidata/llm/<tool>.yaml`: model candidates, effort and picker patterns.
- `home/.chezmoidata/llm/paths.yaml`: directory prefixes for the launch
  wrappers.
- `home/dot_omp/private_agent/modify_config.yml`: native role rendering and
  per-agent role assignments.

Read those files for current assignments. This document describes how they
are selected, not a second copy of the model table.

## Selection order

Rendering and launch are separate. Rendering decides which aliases and
candidates exist. A `~/bin` wrapper can replace only the new session's
model.

`llm/tool-config` renders in this order:

1. Merge provider references, then apply host conditions, owner switches,
   exclusions and protocol compatibility. The merge order is in
   [provider resolution](providers.md).
2. Expand shared model aliases in each candidate.
3. Keep the first candidate whose provider alias resolved. Rendering does
   not probe availability and does not fail over when a request fails.
4. The tool template writes that model into its native config.

An inherited provider only makes models available. Prefer it by placing a
qualified reference in the candidate list. Disabling that provider continues
through the remaining candidates.

For a new session, the wrappers for `pi`, `omp`, `opencode`, `grok`,
`goose`, and `copilot` then choose in this order:

1. Argv that already selects a session: `--model` or `--provider`, resume,
   continue, session, fork, `--help`, `--version`, or a subcommand. The
   wrapper leaves it. OMP `acp` and `launch`, OpenCode `acp` and `run`, and
   Grok `agent` are still new sessions. Goose inserts flags only after
   `session` or `run`.
2. A project pin. Pi reads `.pi/settings.json` `defaultModel`. OMP reads
   `.omp/config.yml` `modelRoles.default`. No other tool has this pin.
3. The longest `paths.yaml` prefix that contains the startup directory.
   OMP and Grok `--cwd`, and OpenCode's project argument, select that
   directory; otherwise it is the working directory. `model` is the
   qualified id; each rule's `paths` groups directory prefixes sharing it.
   Entries are `path.toml` key lists; `[chezmoi, workingTree]` names this
   source checkout.
   Pi, OMP, OpenCode and Grok use the qualified catalog key directly.
   Goose splits only the first slash into its native provider id and the
   intact upstream model id; custom providers use the reserved
   `custom_chezmoi_` namespace. Copilot selects the alias's BYOK endpoint.
   These native spellings belong to the adapters, not directory rules.
4. No matching prefix. Copilot still resolves its own candidate list and
   exports that alias. The other wrappers pass no `--model`, so the
   rendered default remains.

The wrapper does not change other OMP roles or Pi's separate lists. An
unknown id, or a Copilot alias that did not resolve, fails the launch. The
real binary's absolute path skips the wrapper. So does a checkout outside
the prefixes, including `path.data.worktree`.

Pi selects its primary model, session-title model, subagent model, and
web-search summary model from separate lists in `pi.yaml`. OMP exposes
named roles to its call sites. Plugin enablement is separate from provider
resolution: an alias for an extension-backed provider does not load that
extension. Check `home/.chezmoidata/plugins/pi.yaml` when changing such
candidates.

## OMP role policy

The renderer builds `modelRoles.default` from the selected primary model and
effort, then adds `default_models`. Each role may have its own candidate list.

| Role | Responsibility | Selection policy |
| --- | --- | --- |
| `default` | Primary session | General coding capability |
| `slow` | Thorough analysis and security review | Favor depth for infrequent work |
| `smol` | Prewalk and lightweight work | Favor latency and cost |
| `task` | Subagent execution | Balance capability against high output volume |
| `advisor` | Review the primary's changes | Prefer a different model family; avoid paying for unnecessary speed |
| `tiny` | Titles, memory and classification | Use only the effort the task needs |
| `plan` | Architectural planning | Favor reasoning quality over price for infrequent calls |

Role lists lead with company-funded IV candidates and retain personal
subscription candidates for hosts where the IV provider is off. That
provider's host condition chooses the tier; templates must not duplicate that
policy with host-specific role tables.
Effort support is per model, so a personal fallback must use its own valid level.
See [ADR 0006](../adr/0006-omp-model-role-tiers.md).

Leave a role unset when its native fallback already gives the intended model
and effort. Image inspection can fall through from the vision role to the
default role and active model, checking image support at each step. Commit
work can use the active model without a separate assignment.

Per-agent overrides use role aliases rather than model ids. This reuses the
same host selection instead of introducing another model table. Their mapping
and the model-cycle order belong to `modify_config.yml`.

## Changing a selection

- Edit the owning tool data file, not generated agent config.
- Edit `paths.yaml` for a directory default. Do not copy the model into the
  wrappers.
- Qualify model references when multiple aliases can serve the same id.
  Bundled login names and custom aliases have distinct ownership; see
  [ADR 0005](../adr/0005-llm-provider-aliases.md) and
  [ADR 0010](../adr/0010-iv-codex-iv-cc.md).
- Keep selected models and role targets covered by `enabled_models`.
  Use scoped family patterns rather than whole catalogs where appropriate.
- Treat effort, context and Fast variants as provider-specific. Do not copy
  another client's SKU spelling or catalog window without checking its adapter.
  Catalog ownership is described in
  [ADR 0009](../adr/0009-omp-models-dev-overlays.md).
- Validate enabled and disabled provider branches, including the non-IV tier,
  then run `make verify`. Rendering must not make model requests or install tools.
