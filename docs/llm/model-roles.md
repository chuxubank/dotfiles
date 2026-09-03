# OMP model roles

`home/.chezmoidata/llm/omp.yaml` is the source of truth; this file is the
summary. A role is a named model slot OMP resolves at each call site, not a
model name. `home/dot_omp/private_agent/modify_config.yml` renders the data
file's `default_models` into `modelRoles` in `~/.omp/agent/config.yml`.

Every role is a candidate list. The renderer picks the first entry whose
provider alias resolved on this host, so one table covers both tiers: the IV
aliases (`openai`, `anthropic`, `iv-anthropic`, `iv`) are gated on
`host_env: [iv]` and drop out elsewhere, leaving the personal-subscription
entry. IV is company-funded and spends effort freely; the fallback stays
deliberately cheaper. Rationale is in
[ADR 0006](../adr/0006-omp-model-role-tiers.md).

| Role | `iv` host | Other hosts | Consumed by |
| --- | --- | --- | --- |
| `default` | `openai/gpt-5.6-sol:high` | `xai-oauth/grok-4.6:high` | Primary session; `*` selector |
| `slow` | `iv-anthropic/claude-fable-5:high` | `cursor/claude-fable-5-1-medium:medium` | `--slow`, thorough analysis |
| `smol` | `openai/gpt-5.6-luna:medium` | `xai-oauth/grok-4.6:medium` | Prewalk target, background work, vibe `fast` |
| `task` | `openai/gpt-5.6-terra:high` | `xai-oauth/grok-4.6:high` | Subagent default, vibe `good` |
| `advisor` | `anthropic/claude-sonnet-5:medium` | `xai-oauth/grok-4.6:medium` | Per-turn advisor review |
| `tiny` | `openai/gpt-5.6-luna:low` | `xai-oauth/grok-4.6:minimal` | Titles, memory, auto-thinking, stop detection |
| `plan` | `anthropic/claude-opus-5:xhigh` | `cursor/claude-opus-5-high` | `--plan`, architectural planning |

`cycleOrder` is OMP's default `smol → default → slow`, so `Alt+N`/`Alt+P` walk
those three.

## Deliberately unset

`vision` and `commit` carry no assignment.

`inspect_image` resolves `@vision` → `@default` → active model, requiring image
input at each level, and both tiers' `default` already advertises it. Neither
provider bills per image, so there is nothing to route away from. `commit`
falls through to the active model, which is what that flow wants.

Setting a role that would resolve to the same model as its fallback is only
worth it for a different effort level — that is the whole content of `tiny`
against `smol` on the IV tier.

## Why these models

Cost separates models the catalog otherwise presents as equivalent. `sol` and
`terra` are identical on context (372K), max output (128K), and effort levels,
and both cost $1.5 in — but `terra` is $2 out against `sol`'s $12. `task` is the
heaviest output producer in the system, one subagent per delegated slice, so it
takes `terra`. Its smaller context than Sonnet's 1M is affordable because each
subagent starts on a fresh context rather than inheriting the parent's.

`plan` runs about once per session and is the one place where the best available
reasoning outranks price, so it takes `claude-opus-5` at $6/$30 — a rate that
would not survive at `task`'s call volume.

`advisor` stays on Sonnet rather than following `task` to `terra`. It reviews the
primary's own deltas, so it is deliberately a different model family from the
GPT-family `default`; making it cheaper by matching the reviewed family defeats
the role. `slow` keeps `claude-fable-5` even though its $3/$18.5 on the IV alias
is dearer on output than Opus, because that role is explicitly the thorough,
infrequent one.

## Constraints

Pin the provider on any model id more than one alias can serve; a bare id
resolves against the union of every alias's catalog and can silently reach the
wrong endpoint. `gpt-5.6-luna` is served by `anthropic`, `iv`, and `openai`, so
it is written `openai/gpt-5.6-luna` — the `anthropic` alias is the
Anthropic-typed surface on the cc token and must not carry OpenAI-shaped models.
See [ADR 0005](../adr/0005-llm-provider-aliases.md).

Role targets must also appear in `enabled_models`. That list is the picker's
allow-list, and a role pointing outside it resolves to a model the session
cannot select.

Effort suffixes are per model. `gpt-5.6-luna` has no `minimal`; its floor is
`low`.

## Subagents

`task.agentModelOverrides` in `modify_config.yml` assigns role aliases rather
than model ids, so per-agent routing re-resolves per host through the table
above instead of needing a second tier list.

| Agent | Model | Why |
| --- | --- | --- |
| `scout` | `@smol` | Read-only research |
| `sonic` | `@smol` | Mechanical, low-reasoning by definition |
| `security-reviewer` | `@slow` | Depth is the point |
| everything else | `@task` | Bundled default |
