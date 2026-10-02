# Repository instructions

## Keyboard documentation

When changing keyboard shortcuts in the Ghostty, WezTerm, Herdr, or Zellij
configuration, update the terminal/mux summary in `README.org` and the
matching detailed reference in `docs/keybindings/` in the same change.
When changing Pi or OMP keybindings, update the in-pane summary in
`README.org`, the shared Emacs set in `docs/keybindings/agents/README.md`, and
the tool file (`agents/pi.md` / `agents/omp.md`). Include both the tool default
and the current assignment, and mark deliberate changes prominently. Treat the
configuration files as the source of truth and keep the summary concise.

Run `make verify` after modifying keyboard configuration or its documentation.

## Template boundaries

Inline single-consumer rendering and transformation logic in its target
file, including `modify_` templates. Extract an `includeTemplate` only when it
serves multiple consumers or owns an independent contract worth testing. A
template that only forwards arguments, performs one local filter, or lightly
reshapes data for one target belongs at the call site.

## Chezmoi script retry boundaries

A `run_onchange` script is chezmoi's success-recording and retry unit. Split
independently retryable work into separate scripts by ecosystem or transaction
domain; keep ordered or dependent commands together. Put foundational, stable
work before slower or failure-prone work, because a failed script can prevent
later scripts from running in that apply. Prefer these native script boundaries
over custom checkpoint state. Validate changes by rendering each affected
template, checking its shell syntax and success/failure exit status, and running
`make verify`; do not invoke the real operations during validation.

## External repo definitions

`home/.chezmoidata/path.toml` owns path strings only.
`home/.chezmoidata/repositories.yaml` maps those paths to git clone metadata;
add every managed git repository there rather than writing another external
template. `home/.chezmoiexternals/repositories.toml.tmpl` is the single
renderer. Keep entries in `path.toml` namespace/key order. Platform-, app-, or
file-specific non-git externals remain in their existing specialized files.
The rationale is in
`docs/adr/0004-repository-metadata.md`.

Private or host-specific repositories need a `when` condition that excludes
inapplicable hosts. The renderer uses the shared host-condition evaluator, so
use the same `when.enabled` / `when.disabled` schema as other data files.
chezmoi merges all externals into one namespace and a duplicated destination
is silently last-wins, so verify the rendered destinations are unique.

## LLM provider aliases

Pi and OMP name IV token surfaces the same way Codex and Hermes do.
`iv-codex` is the codex token, `iv-cc` is the cc token, and `iv` is the
default token's OpenAI surface. `iv-anthropic` is that same default token
on the Anthropic protocol and only serves `claude-fable-5`. The bundled
names `openai` and `anthropic` stay free for `/login`. `iv-codex` and
`iv-cc` are not bundled providers: each catalog is the enumerated IV list
plus models-dev metadata. opencode, craft-agents, and claude-code keep
`openai` / `anthropic` as their own provider keys; they do not share Pi's
`auth.json`. An alias the tool does not ship has no bundled card to inherit.

Because our entries merge into the bundled catalog instead of replacing it, one
model id can exist on several providers and a bare id resolves against the
union, reaching a different provider with no error. Pin the provider on any id
more than one alias can serve. Pi's `enabled_models` generation globs stay
unprefixed (`gpt-6*`, `claude-opus-5*`) so every copy stays in the picker.
OMP pins the provider on those same globs. Role and default model refs stay
qualified. Omit OpenRouter on pi, omp,
hermes, and opencode: `models: false` still injects the API key and enables
the bundled catalog, so a bare id can resolve there instead of IV or the
subscription fallback. Tools that actually route through it (goose, gptel)
keep the alias. The rationale is in
`docs/adr/0005-llm-provider-aliases.md` and
`docs/adr/0010-iv-codex-iv-cc.md`.

## OMP model roles

`default_models` in `home/.chezmoidata/llm/omp.yaml` owns the role table, and
`home/dot_omp/private_agent/modify_config.yml` renders it into `modelRoles`.
Each role is a candidate list resolved by first surviving provider alias: lead
with an IV entry, which is company-funded and may spend effort freely, and
follow with the personal-subscription entry that applies off `iv`. Do not add a
`host_env` conditional to the template for this; the alias gating already
carries it. Role targets must also be listed in `enabled_models`, or the role
resolves to a model the picker cannot select.

Update the resolved two-tier table in `docs/llm/model-roles.md` in the same
change, treating the data file as the source of truth. Verify the non-`iv` tier
explicitly — the working host only exercises one branch:

```sh
chezmoi execute-template '{{- $c := includeTemplate "llm/tool-config" (mergeOverwrite (deepCopy .) (dict "tool" "omp" "host_env" "personal")) | fromJson -}}
{{ range $r, $m := $c.default_models }}{{ $r }}={{ $m }}
{{ end }}'
```

Prefer leaving a role unset over assigning what its fallback chain would reach
anyway; an assignment earns its place by changing the model or the effort.
Effort levels are per model, so a fallback cannot assume its IV sibling's level.
The rationale is in `docs/adr/0006-omp-model-role-tiers.md`.

## OMP catalog overlays

When `models: false`, OMP copies the models.dev card onto the exact model
id through `model-config/omp` (SuperGrok today). Keep list prices visible on
subscriptions: the catalog numbers are still the comparison the role table
uses. Do not add a field-allowlist or a $0 special case for subscriptions.
Effort-sibling copies take `cost`, so a live name or window is not replaced
by the first-party stem.

OMP's Cursor provider gets no overlay: its bundled catalog plus live
discovery already price every served id, including Fast lanes and context
SKUs (`grok-4.7-500k-fast`, `claude-opus-5-1m`). Overlaying models.dev
there replaced Cursor's windows with the vendor API's. Pi's `pi-cursor-sdk`
prices everything at $0, so `llm.catalogs.cursor`
(`home/.chezmoidata/llm/cursor.yaml`) carries the Cursor rates Pi projects
onto its ids; Fast rates come only from `fast`. Cursor picker globs live on
`llm.providers.cursor.enabled_models`. The rationale is in
`docs/adr/0009-omp-models-dev-overlays.md`.
