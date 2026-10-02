# OMP model roles

`home/.chezmoidata/llm/omp.yaml` is the source of truth; this file is the
summary. The shared primary model is `${gpt_primary}`, declared once in
`home/.chezmoidata/llm/common.yaml`; references below intentionally keep that
alias so changing the primary does not require editing this document. A role is a named model slot OMP resolves at each call site, not a
model name. `home/dot_omp/private_agent/modify_config.yml` renders the data
file's `default_models` into `modelRoles` in `~/.omp/agent/config.yml`.

Every role is a candidate list. The renderer picks the first entry whose
provider alias resolved on this host, so one table covers both tiers: the IV
aliases (`openai`, `anthropic`, `iv-anthropic`, `iv`) are gated on
`host_env: [iv]` and drop out elsewhere, leaving the personal-subscription
entry. The `cursor` provider is the reverse: disabled on iv, so no Cursor
model reaches the IV tier or its picker. IV is company-funded and spends
effort freely; the fallback stays
deliberately cheaper. Rationale is in
[ADR 0006](../adr/0006-omp-model-role-tiers.md).

Pi does not use this table. Its personal default is
`cursor/${grok_primary}@256k:fast` because `pi-cursor-sdk` posts `context`,
`reasoning_effort`, and `fast` on registry id `${grok_primary}`, and Cursor's
run registry rejects `context=500k` (`Invalid parameters for registry model`
/ `AI Model Not Found`). `models.list()` still advertises that window, and
local validation only checks the id. `context=256k` completes; `context=500k`
alone is rejected too. OMP's `cursor/${grok_primary}-500k-fast` is a different
SKU and is unaffected. See
[ADR 0009](../adr/0009-omp-models-dev-overlays.md).

| Role      | `iv` host                          | Other hosts                             | Consumed by                                   |
|-----------|------------------------------------|-----------------------------------------|-----------------------------------------------|
| `default` | `openai/${gpt_primary}:high`        | `cursor/grok-4.7-500k-fast:high`        | Primary session; `*` selector                 |
| `slow`    | `iv-anthropic/claude-fable-5:high` | `cursor/claude-opus-5-5:medium`         | `--slow`, thorough analysis                   |
| `smol`    | `openai/gpt-6-luna:medium`         | `cursor/composer-2.5-fast`              | Prewalk target, background work, vibe `fast`  |
| `task`    | `openai/${gpt_primary}:medium`      | `xai-oauth/grok-4.7:high`               | Subagent default, vibe `good`                 |
| `advisor` | `anthropic/claude-sonnet-5`        | `cursor/composer-2.5`                   | Per-turn advisor review                       |
| `tiny`    | `openai/gpt-6-luna:low`            | `xai-oauth/grok-4.7:minimal`            | Titles, memory, auto-thinking, stop detection |
| `plan`    | `anthropic/claude-opus-5:xhigh`    | `cursor/claude-opus-5-1m:high`          | `--plan`, architectural planning              |

`cycleOrder` is OMP's default `smol → default → slow`, so `Alt+N`/`Alt+P` walk
those three.

Pi uses the same candidate order and the same Cursor families, but
`pi-cursor-sdk` ids are not these SKUs. Personal `default` is
`cursor/grok-4.7@256k:fast`: the Fast lane on the 256k window. The SDK
default window is 500k (`cursor/grok-4.7@500k:fast`), which is OMP's
`cursor/grok-4.7-500k-fast`, but Cursor rejects that window from the SDK
(ADR 0009). OMP only keeps that window while
`extendedContext` is on; `modify_config.yml` sets it. Off clamps Cursor to
the bundled long-context threshold, 256k. Pi cannot set Grok's `reasoning_effort`.
OMP's `claude-opus-5-1m` is `cursor/claude-opus-5@1m`. Composer Fast is
`cursor/composer-2.5:fast` (the unsuffixed id is also fast, because that is
the SDK default); standard Composer is `cursor/composer-2.5:slow`. Opus 5.5
is `cursor/claude-opus-5-5@1m`. Pi has no `slow` role, so that id is only on
the picker allow-list. OMP prices Cursor from its own catalog. Pi's
prices are `llm.catalogs.cursor` in `home/.chezmoidata/llm/cursor.yaml`,
projected onto extension ids. `longContext` becomes
`cost.tiers`. The unsuffixed Pi id bills the fast card when that is the SDK
default (Grok, Composer); `:slow` bills the stem.

## Deliberately unset

`vision` and `commit` carry no assignment.

`inspect_image` resolves `@vision` → `@default` → active model, requiring image
input at each level. Both tiers' `default` advertise it: IV through `${gpt_primary}`,
and personal through `cursor/grok-4.7-500k-fast`, which OMP's Cursor
catalog lists with image input. Neither provider bills per image. `commit` falls
through to the active model, which is what that flow wants.

Setting a role that would resolve to the same model as its fallback is only
worth it for a different effort level. On the IV tier that is `tiny` against
`smol`, and `task` against `default`.

## Why these models

`default` tracks the shared `gpt_primary` pin at `:high`. `task` uses the
same id at `:medium`, and Pi's `subagent_model` tracks the same pin. The personal fallback stays `xai-oauth/grok-4.7:high`. Each
subagent starts on a fresh context.

`plan` runs about once per session and is the one place where the best available
reasoning outranks price, so it takes `claude-opus-5` at $6/$30 — a rate that
would not survive at `task`'s call volume.

`advisor` stays on Sonnet. It reviews the primary's own deltas, so it is a
different model family from the GPT-family `default`. The personal fallback is
Composer 2.5, which sits in Cursor's
first-party pool rather than SuperGrok — the standard SKU, not Fast. Fast is
`smol`'s interactive execution lane ($3/$15); advisor reviews in the background
and a late note still lands on the current primary, so the cheaper standard
rate ($0.5/$2.5) is enough. Personal `default` is Cursor Grok 4.7 Fast on the 500k window; tokens past 256k bill the long-context Fast rate.

`slow` stays `claude-fable-5` on IV, at `:high`, because that role is the
thorough, infrequent one and the cc group 404s the id — it only resolves on
`iv-anthropic`. The personal fallback is `cursor/claude-opus-5-5:medium`
($4/$20). Cursor serves that as one id with an effort ladder, not a per-effort
SKU, so the suffix is `:medium` rather than an `-medium` id.

## Constraints

Pin the provider on any model id more than one alias can serve; a bare id
resolves against the union of every alias's catalog and can silently reach the
wrong endpoint. `gpt-6-luna` is written `openai/gpt-6-luna`. The `anthropic`
alias is the cc token's Anthropic surface, and its allow-list is Claude ids.
GPT ids stay on `openai/gpt-6*`.
See [ADR 0005](../adr/0005-llm-provider-aliases.md).

Role targets must also appear in `enabled_models`. That list is the picker's
allow-list, and a role pointing outside it resolves to a model the session
cannot select. Entries are generation globs (`gpt-6*`,
`claude-opus-5*`, `claude-fable-5*`, `grok-4.7*`, `muse-spark-1.3*`,
`gemini-3.8-flash*`, `deepseek-v4*`, `glm-5.3*`, `kimi/kimi-k3*`), not whole
catalogs, so older lines stay out while personal-host `plan` and `slow` still
match `claude-opus-5*`. IV `slow` is the exact `iv-anthropic/claude-fable-5`
pin; `cursor/claude-fable-5*` stays a manual pick. `deepseek-v4*`,
`glm-5.3*`, and `kimi/kimi-k3*` are `iv`-pinned and carry no role: they are
manual picks, and they drop out with the alias on
non-`iv` hosts. `muse-spark-1.3*`, `gemini-3.8-flash*`, and `cursor/default`
(Auto) are Cursor-pinned manual picks. `kimi/kimi-k3*` keeps its vendor segment because the endpoint
returns the id that way; a leading segment counts as a provider only when it
names a configured alias.

Effort suffixes are per model. `gpt-6-luna` has no `minimal`; its ladder
starts at `none`, and `tiny` stays at `:low`.

## Subagents

`task.agentModelOverrides` in `modify_config.yml` assigns role aliases rather
than model ids, so per-agent routing re-resolves per host through the table
above instead of needing a second tier list.

| Agent               | Model   | Why                                     |
|---------------------|---------|-----------------------------------------|
| `scout`             | `@smol` | Read-only research                      |
| `sonic`             | `@smol` | Mechanical, low-reasoning by definition |
| `security-reviewer` | `@slow` | Depth is the point                      |
| everything else     | `@task` | Bundled default                         |
