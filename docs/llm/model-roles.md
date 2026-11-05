# Model selection and OMP roles

## Sources of truth

- `home/.chezmoidata/llm/common.yaml`: shared model aliases and provider definitions.
- `home/.chezmoidata/llm/<tool>.yaml`: model candidates, effort and picker patterns.
- `home/.chezmoidata/llm/paths.yaml`: directory prefixes for the Pi and OMP
  launch wrappers.
- `home/dot_omp/private_agent/modify_config.yml`: native role rendering and
  per-agent role assignments.

Read those files for current assignments. This document describes how they
are selected, not a second copy of the model table.

## Selection flow

1. `llm/tool-config` merges provider references and applies host conditions,
   owner switches, exclusions and protocol compatibility. See
   [provider resolution](providers.md).
2. Shared model aliases are expanded in each candidate.
3. Each candidate list selects the first entry whose provider alias resolved.
   This happens during rendering; it does not probe model availability or
   provide request-time failover when an endpoint fails.
4. The tool's template writes the selected model into its native config.

An inherited provider only makes models available. To prefer it, place a
qualified model reference in the tool's candidate list. Disabling that
provider lets selection continue through the remaining candidates.

Pi selects its primary model, session-title model and subagent model from
separate lists in `pi.yaml`. OMP instead exposes named roles to its call sites.
Plugin enablement is separate from provider resolution: an alias for an
extension-backed provider does not load that extension. Check
`home/.chezmoidata/plugins/pi.yaml` when changing such candidates.

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
subscription candidates for other hosts. Provider host conditions choose the
tier; templates must not duplicate that policy with host-specific role tables.
Effort support is per model, so a personal fallback must use its own valid level.
See [ADR 0006](../adr/0006-omp-model-role-tiers.md).

Leave a role unset when its native fallback already gives the intended model
and effort. Image inspection can fall through from the vision role to the
default role and active model, checking image support at each step. Commit
work can use the active model without a separate assignment.

Per-agent overrides use role aliases rather than model ids. This reuses the
same host selection instead of introducing another model table. Their mapping
and the model-cycle order belong to `modify_config.yml`.

## Directory defaults

`llm/paths.yaml` assigns a model to a `path.toml` prefix. `model` is the Pi, OMP, OpenCode, and Copilot id. A `tools` entry
replaces it for a command whose CLI uses a different spelling. `~/bin` wrappers for `pi`, `omp`,
`opencode`, `grok`, `goose`, and `copilot` are ahead
of the real binaries on `PATH` and exec those binaries. The longest prefix
containing the startup directory wins. OMP and Grok `--cwd`, and OpenCode's
project argument, select that directory; otherwise it is the process working
directory. Goose inserts `--provider` and `--model` after `session` or `run`.

The wrapper passes the model only for a new session. It leaves the rendered
global default, other OMP roles, and Pi's subagent model alone. These argv
shapes are not rewritten: an existing `--model` or `--provider`, resume,
continue, session, and fork flags, `--help` / `--version`, and a subcommand.
Session entry points still receive the prefix model: OMP `acp` and `launch`,
OpenCode `acp` and `run`, and Grok `agent`. A project
`.pi/settings.json` `defaultModel` or `.omp/config.yml` `modelRoles.default`
wins over the prefix. A directory outside every prefix keeps that global default. Copilot
still applies it: the wrapper resolves the qualified id against
`llm/copilot.yaml` and exports `COPILOT_PROVIDER_*` for that alias. The
other wrappers pass no `--model`. An unknown id, or a Copilot alias that
did not resolve, fails the launch instead of falling through.

Invoking the real binary by its absolute path skips the wrapper. Checkouts
outside the configured prefixes, including `path.data.worktree`, do too.

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
