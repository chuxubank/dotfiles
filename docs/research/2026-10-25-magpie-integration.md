# Magpie against this chezmoi LLM layer

**Date:** 2026-10-25
**Question:** How does current magpie relate to this repo's LLM configuration, and what integration is possible without two writers on the same files?
**Method:** [yetone/magpie](https://github.com/yetone/magpie) tag `v0.1.1477` (published 2026-10-25, `target_commitish` `main`) for `docs/reference.md`, `docs/integrating.md`, and `internal/agent`. The README was read from `main` the same day; the release notes point at that tag. Install facts are from [yetone/magpie-releases](https://github.com/yetone/magpie-releases/blob/main/README.md). Local facts are from `home/.chezmoidata/` and the destination templates. `rg` found no `magpie` or `yetone` declaration in this repo before this note. `magpie` is not on `PATH`. No magpie process was run, and no live config was opened.

## Recommendation

Do not let magpie's Agents page write config. Magpie is a second writer of the model and provider keys this repo already renders from `home/.chezmoidata/llm/`.

**Decision:** one gateway, on VPS `bwg-cn2-gia`, not per machine and not over Tailscale. Chezmoi does not install the formula or a launchd unit, and it does not write `http://127.0.0.1:3425`. While the `magpie` tool is on, Codex, Pi, OMP, OpenCode, Hermes, and craft-agents get `https://magpie.<VPS domain>`; OpenAI-compatible bases add `/v1`, and an Anthropic or Gemini type keeps the origin. While the tool is off, those tables drop the alias. Defaults and OMP roles stay on IV or the personal subscription. Goose, Grok Build, and Cursor CLI are not given the alias. Pi, OMP, and Codex read that key with `pass-field`. OpenCode's `auth.json` and Hermes's provider entry have no command field, so those two still receive the key; OpenCode's auth file is mode `0600`. Upstream keys stay in the VPS `~/.config/magpie/providers.json`, which chezmoi does not manage or purge. Caddy on that VPS reverse-proxies the name at the host's `127.0.0.1:3425` without publishing that port, without `basic_auth`, and without `MAGPIE_TRUST_PROXY`.

There is no upstream mode that stores providers and then refuses to edit agent files. Providers live in `~/.config/magpie/providers.json` until a model is picked. Picking one always rewrites that agent's config. `docs/reference.md` and `docs/integrating.md` do not mention chezmoi, git-managed configs, or a read-only / do-not-manage switch. Searched the reference for those words: the only "read only" hit is the OpenCode import dialog, which reads `auth.json` and does not write it.

Installing the formula or the cask without opening the Agents page does not add a capability this machine lacks, and the app's job is to edit those files. A trial belongs in a scratch `HOME`. It must not touch the real `~/.codex`, `~/.pi`, `~/.omp`, `~/.config/opencode`, `~/.config/goose`, `~/.grok`, or `~/.cursor`.

`docs/adr/0007-agent-integration-lifecycle.md` is the lifecycle for one tool injecting hooks into another agent's tree. Magpie is not that. A `tools.yaml` entry would only be a package. Using magpie as the model switcher replaces the `llm/*.yaml` render, which that ADR does not describe.

On this Mac the package shape, if it were ever added, would be the formula `magpie`, not the cask. The menu bar is optional, and the cask's app updates itself outside `brew upgrade`. Do not use `curl | sh`. Neither package is recommended, because the binary's purpose is the rewrite.

What would have to leave chezmoi before magpie could own models is listed at the end. Until that handoff is the goal, magpie stays out.

## What current magpie is

`v0.1.1477` is still the menu-bar switcher plus a local gateway. The reference's opening says the gateway is `http://127.0.0.1:3425/v1` and that a picked model is served from there. [integrating.md](https://github.com/yetone/magpie/blob/v0.1.1477/docs/integrating.md) says the bind is `127.0.0.1:3425`, or the `port` field of `~/.config/magpie/settings.json`, and that `GET /api/hello` identifies it. `MAGPIE_ADDR` moves it.

The same page lists the protocols: `/v1/chat/completions`, `/v1/responses`, `/v1/messages`, and Gemini `/v1beta/models/{model}:generateContent`. The reference's "Connecting anything else" table matches that, and adds speech-to-text. The README on `main` says the same four families, including Responses.

A model chosen from magpie's catalog is `provider/model` on that gateway. The reference states that agents then do not hold the vendor key or the vendor URL. Pointing an agent at a vendor directly is what you get by not connecting it. The adapter can also write a native model id (Pi's `ownOptions`, OpenCode returning the value unchanged). That uses the agent's own provider. It is not magpie writing a vendor base URL for a catalog model.

When the gateway process stops, connected agents lose it. The reference says the TUI serves the gateway only while it is open and that agents lose it when it quits. `magpie serve` and `magpie daemon install` are the headless processes. Routing-group failover runs inside the gateway. It does not run if nothing is listening on 3425. There is no documented agent-side fallback to the vendor URL.

Edits are surgical for the keys the adapter sets. [internal/edit/json.go](https://github.com/yetone/magpie/blob/v0.1.1477/internal/edit/json.go) says `SetJSON` preserves comments, key order, and indentation. [internal/edit/toml.go](https://github.com/yetone/magpie/blob/v0.1.1477/internal/edit/toml.go) says magpie owns the tables it writes and replaces those tables verbatim, and every other line stays. That is not a shared-file protocol with chezmoi. Both can preserve the keys they do not manage. They overwrite the keys they both manage. The last writer wins those keys. A chezmoi `modify_*` apply puts the managed set back. A later magpie `Set` or `Sync` puts magpie's set back.

`Sync` rewrites the magpie provider block of an agent that is already connected. Simply adding a provider does not. `magpie restore --no-agents` restores providers and settings and leaves agent files as they are ([reference, Moving to another machine](https://github.com/yetone/magpie/blob/v0.1.1477/docs/reference.md)). That is a restore flag, not a resident read-only mode.

## State, secrets, and discovery

`~/.config/magpie` is the state directory. `XDG_CONFIG_HOME` is honored. From the reference's Files section:

- `providers.json` holds providers, keys included, mode `0600`.
- `profiles.json` holds profiles. `magpie use` writes those snapshots back into agent files.
- `logins.json`, `plugin-auth.json`, `mcp-signins.json`, and `caller-keys.json` are sign-ins and gateway keys, mode `0600` where the reference says so.
- `stash.json` is the previous agent values, restored on disconnect.
- `applied.json` is what magpie last set.

Subscription discovery is on unless turned off. The README says magpie reads Claude Code's and Codex's sign-in files and the Keychain, and that Settings → Privacy → *Subscription accounts*, `magpie accounts discovery off`, or `MAGPIE_NO_ACCOUNTS=1` stops that. The reference's "Signed-in agents as providers" says magpie refreshes those tokens the way the agent does and writes a rotated token back where the agent will find it. That write does not require a model pick. `readOwnAuth` in [internal/agent/agents.go](https://github.com/yetone/magpie/blob/v0.1.1477/internal/agent/agents.go) skips the auth file when discovery is off.

Import of Codex providers requires an inline `experimental_bearer_token`. Entries that only name an `env_key` are skipped. This repo's Codex template uses `auth.command` (`bin/pass-field`), not an inline token, so that import does not pick up the chezmoi providers. OpenCode's import reads `~/.local/share/opencode/auth.json` and the reference says magpie never writes that file. The chezmoi template `home/dot_local/share/opencode/auth.json.tmpl` writes `auth_key` from `llm/tool-config` into that file. `auth_key` is the resolved API key. Magpie's import would copy it into `providers.json`. This note did not open the live file.

The README's Library writes instructions, MCP servers, skills, and subagents into each agent's files and removes only what it wrote. [internal/library/mcp.go](https://github.com/yetone/magpie/blob/v0.1.1477/internal/library/mcp.go) is that writer. It is a second collision with this repo's MCP and plugin templates, separate from the model keys, and only if the Library is used.

## Can magpie express this repo's model policy?

| Need | In magpie v0.1.1477 |
|---|---|
| (a) Per-role ordered fallbacks | No, as a live role value. [internal/agent/omp.go](https://github.com/yetone/magpie/blob/v0.1.1477/internal/agent/omp.go) treats a comma-separated `modelRoles` value as the user's own list (`ompSplit` returns one model only when there is no comma). Picking a magpie model replaces that role with one `magpie/<provider>/<model>` and an optional `:level`. The old list is stashed and comes back on reset. Routing groups (`smart`, `order`, `rotate`, `usage`, `pace`, `weight`) fail over inside the gateway. They are not a per-role list and they do not change with `host_env`. |
| (b) Per-model effort | Partially, and not the way `omp.yaml` does it. Codex, Pi, OMP, Goose, Grok, Hermes, and Copilot have an effort field. OMP keeps one `:level` on the single model it wrote. models.dev fills reasoning levels. A role cannot carry IV at `:high` and a personal fallback at `:medium` at the same time, because the fallback list is no longer the role value. Effort is per model in this repo, so that matters. See `docs/adr/0006-omp-model-role-tiers.md`. |
| (c) `host_env` aliases | No. IV providers in `home/.chezmoidata/llm/common.yaml` are `when.enabled.host_env: [iv]`. Magpie profiles are a manual snapshot of every agent's current fields (`magpie save` / `magpie use`). Nothing in the reference applies a profile because the host is `iv` or `personal`. |
| (d) Catalog price overlays | Not these overlays. The reference's "What a model costs" prices usage from a user price, else the provider catalogue, else models.dev. It does not copy a models.dev card onto an OMP model id, and it does not apply `llm/cursor.yaml` Fast rates. OMP's Cursor provider is left un-overlaid on purpose (`docs/adr/0009-omp-models-dev-overlays.md`). Magpie's Cursor CLI adapter does not list gateway models at all. |
| (e) Several tokens, one base URL | As several providers, yes. `magpie provider add` takes `url=` and `key=` per provider, and `anthropic=` for an Anthropic base, or both. `iv`, `iv-codex`, and `iv-cc` are three tokens (`docs/adr/0010-iv-codex-iv-cc.md`). They would be three magpie providers. `iv-anthropic` is the default token on the Anthropic protocol and only `claude-fable-5`; a provider with `anthropic=` and `models=claude-fable-5` can say that. The documented `magpie provider key <id> <key>` replaces the key. The README says each key can have its own proxy, which implies more than one key on a provider. The reference section read for this note does not document the command that adds the second key. Subscriptions are the documented multi-credential failover, and they are OAuth accounts, not these three tokens. Nothing gates a provider on `host_env`. |

Pi `enabled_models` globs in `home/.chezmoidata/llm/pi.yaml` stay unprefixed (`gpt-6*`, `claude-opus-5*`). OMP's globs in `omp.yaml` are provider-pinned. Magpie's Pi adapter appends the picked `magpie/...` id to `enabledModels` when a list exists and no pattern matches ([internal/agent/pi.go](https://github.com/yetone/magpie/blob/v0.1.1477/internal/agent/pi.go), `piScopeWith`). It does not own the glob list. Chezmoi's modify template writes the whole `enabledModels` array, so the next apply drops the appended id.

OpenRouter stays omitted on pi, omp, and opencode because `models: false` still injects a key (`docs/adr/0005-llm-provider-aliases.md`). Magpie has an OpenRouter preset. Connecting an agent to it would put OpenRouter back in front of the bundled catalog. Goose is one of the tools that is allowed to keep the alias. Magpie would still route Goose through the gateway rather than through that alias.

## Collision inventory

Enabled means the `tools.yaml` entry is not `when: {enabled: false}`. `codex`, `cursor`, `goose`, `github-copilot`, `omp`, `opencode`, and `pi` use `non_ci` (`disabled: {host_env: [ci]}`). `grok` has no `when`, so it is on for every host. `claude-code`, `gemini-cli`, `hermes`, and `openclaw` are off. `policies.purge_disabled_tools` is on (`docs/adr/0001-remove-vs-purge.md`), so a disabled tool's `purge` paths are removed on apply.

Checked the same day, without reading contents: `~/.config/opencode/opencode.json` exists and `opencode.jsonc` does not, so magpie's OpenCode adapter and chezmoi share that path. Both `~/.config/cursor/cli-config.json` and `~/.cursor/cli-config.json` exist. Both `~/.config/zed/settings.json` and `~/.config/zed/config.json` exist. `~/.config/magpie` does not.

| Agent | Enabled here? | Chezmoi dest path(s) | Writer kind | Magpie path and fields | Same file? |
|---|---|---|---|---|---|
| Codex | yes, non-ci | `~/.codex/config.toml`, `~/.codex/model-catalog.json` | config is `modify_private_config.toml`. Owns `model`, `model_reasoning_effort`, `model_provider`, `model_catalog_json` (points at `model-catalog.json`), and replaces `model_providers`. Catalog file is a full template | `~/.codex/config.toml`: `model`, `model_reasoning_effort`, `model_provider = "magpie"`, `[model_providers.magpie]` (`base_url`, `experimental_bearer_token`), `model_catalog_json` → `~/.codex/magpie-models.json`. Signed-in ChatGPT path sets `openai_base_url` to the gateway instead. [codex.go](https://github.com/yetone/magpie/blob/v0.1.1477/internal/agent/codex.go) | yes, `config.toml`. The two catalog files differ. The pointer key does not |
| Pi | yes, non-ci | `~/.pi/agent/settings.json`, `~/.pi/agent/models.json` | settings is modify (`defaultProvider`, `defaultModel`, `defaultThinkingLevel`, `enabledModels`, plus tools, retry, theme, packages). `models.json.tmpl` is a full file. `apiKey` is `!command` `pass-field` | `settings.json`: `defaultProvider`, `defaultModel`, `defaultThinkingLevel`, and an appended `enabledModels` entry. `models.json`: `providers.magpie` with `baseUrl` and `apiKey`. [agents.go](https://github.com/yetone/magpie/blob/v0.1.1477/internal/agent/agents.go) `piLikeKeyed` | yes, both |
| omp | yes, non-ci | `~/.omp/agent/config.yml`, `~/.omp/agent/models.yml` | config is modify and replaces `modelRoles`. Also owns `enabledModels` and `disabledProviders`. `models.yml.tmpl` is a full file, `!command` keys | `config.yml`: `modelRoles.default`, `task`, `smol`, `slow`, `plan`, `vision`, `advisor`, `commit`, `tiny`, `memory`, and `defaultThinkingLevel`. Also rewrites `retry.fallbackChains`, `enabledModels`, and `task.agentModelOverrides` when they name a magpie model. `models.yml`: `providers.magpie`, `auth: none`, loopback `baseUrl`. [omp.go](https://github.com/yetone/magpie/blob/v0.1.1477/internal/agent/omp.go) | yes, both |
| OpenCode | yes, non-ci | `~/.config/opencode/opencode.json`, `~/.local/share/opencode/auth.json` | `opencode.json` is modify. Owns `model` and `small_model` and replaces `provider` and `mcp`. `auth.json.tmpl` is a full file of resolved keys | `opencode.json` (first of `.jsonc`, `.json`, `config.json` that exists): `model`, `small_model`, `provider.magpie`. Auth file is read, not written, by the import dialog | yes, `opencode.json`. Not `auth.json` |
| Goose | yes, non-ci | `~/.config/goose/config.yaml` | modify. The managed map from `agent/goose.yaml` includes `GOOSE_MODEL`, `GOOSE_PROVIDER`, and `*_HOST`, and replaces `extensions` | same file: `GOOSE_PROVIDER` / `GOOSE_MODEL` or `active_provider`, plus `GOOSE_THINKING_EFFORT`. Also `~/.config/goose/custom_providers/magpie.json`, which chezmoi does not manage. [goose.go](https://github.com/yetone/magpie/blob/v0.1.1477/internal/agent/goose.go) | yes, the yaml |
| Grok Build | yes | `~/.grok/config.toml` | modify. Owns `models.default` (`${grok_primary}-build-fast`) and `model.<id>.context_window`. Replaces `mcp_servers` and plugin keys. Does not own `features` | same file: `models.default`, `models.default_reasoning_effort`, `features.campaigns = false`, and one `[model."magpie/<provider>/<model>"]` table per catalog model, `base_url` and `api_key` inside the table. [grok.go](https://github.com/yetone/magpie/blob/v0.1.1477/internal/agent/grok.go) | yes |
| Cursor CLI | yes, non-ci | `~/.config/cursor/cli-config.json` | modify. Owns `model.modelId`, `selectedModel` parameters (context `500k`, effort `high`, fast), `hasChangedDefaultModel`, `maxMode`. The template says the CLI reads `$XDG_CONFIG_HOME/cursor` and that `environment.yaml` sets that to `~/.config`, and that `~/.cursor/cli-config.json` is not read. `environment.yaml` does set `XDG_CONFIG_HOME` to `~/.config` | hardcoded `~/.cursor/cli-config.json`: `model.modelId`, `model.displayModelId`, `model.displayName`, `hasChangedDefaultModel`. `cursor()` in `agents.go` offers only `auto`. It does not add a gateway provider | no |
| Copilot CLI | tool on (non-ci), no model file | none. `purge` is `.copilot/**` only if the tool is later disabled | none | `~/.copilot/settings.json`: `model`, `effortLevel`. [agents.go](https://github.com/yetone/magpie/blob/v0.1.1477/internal/agent/agents.go) `copilot` | no chezmoi writer. The file is absent today |
| Claude Code | no | `~/.claude/settings.json` is in `remove`. `purge` is `.claude/**` | modify when the tool is on: whole `env` (including `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN`), `model`, `effortLevel`, permissions, status line, plugins | same `settings.json`: `env` base URL, auth token, and the opus/sonnet/haiku/fable model variables. [claude.go](https://github.com/yetone/magpie/blob/v0.1.1477/internal/agent/claude.go). `~/.claude/settings.json` is absent today | yes, the path. While the tool stays off, apply deletes it |
| Hermes | no | `~/.hermes/config.yaml` is in `remove`. `purge` is `.hermes/**` | modify when on: `model.default`, `model.provider`, and replaces `providers` | same file, and each `profiles/*/config.yaml`: `model.provider`, `model.default`, `providers.magpie`. [hermes.go](https://github.com/yetone/magpie/blob/v0.1.1477/internal/agent/hermes.go). The file is absent today | yes, the path. While the tool stays off, apply deletes it |
| Gemini CLI | no | no model file. Managed file is `~/.gemini/antigravity-cli/mcp_config.json`. `purge` is `.gemini/**` | — | `~/.gemini/settings.json` (`model.name`, `security.auth.selectedType`) and `~/.gemini/.env` (`GOOGLE_GEMINI_BASE_URL`, `GEMINI_API_KEY`). [gemini.go](https://github.com/yetone/magpie/blob/v0.1.1477/internal/agent/gemini.go). Absent today | not the MCP file. Purge would delete magpie's files while the tool stays off |
| Zed | not a `tools.yaml` agent | `~/.config/zed/config.json` (editor layout, `agent.favorite_models`, `agent.model_parameters`) | full file, not a modify template | `~/.config/zed/settings.json`: `language_models.openai_compatible.magpie` and `agent.default_model`. [zed.go](https://github.com/yetone/magpie/blob/v0.1.1477/internal/agent/zed.go). Both files exist | no |
| Crush | not declared | none | — | `~/.config/crush/crush.json` (`providers.magpie`, `models.large`, `models.small`) and the data file under `~/.local/share/crush/crush.json` | no |
| Cline | not declared | none | — | `~/.cline/data/settings/providers.json` (`openai-compatible`) and `models.json`. [cline.go](https://github.com/yetone/magpie/blob/v0.1.1477/internal/agent/cline.go) | no |
| MiMo Code | not declared | none | — | `~/.config/mimocode/mimocode.json(c)`: `model`, `small_model`, `provider.magpie`. Same shape as OpenCode | no |
| OpenClaw | no. `purge` is `.openclaw/**` | none | — | not in the reference Agents table and not in the `agents.go` constructors read for this note | no |
| craft-agents | template exists, not a `tools.yaml` name | `~/.craft-agent/config.json` | full `config.json.tmpl`, `llmConnections` from `llm/craft-agents.yaml`. The file exists | no Craft row in the Agents table | no |
| Cursor Private Inference | not declared | none | — | no config file. Sets `CURSOR_LOCAL_AGENT_BASE_URL` and a gateway key in the user environment. [cursorlocal.go](https://github.com/yetone/magpie/blob/v0.1.1477/internal/agent/cursorlocal.go). Only if that build is installed | no |
| Grok App | not the `grok` tool | none under the app data dir. The tool owns `~/.grok` | — | `~/Library/Application Support/com.grokapp.grok-app/.../config.toml`, not `~/.grok/config.toml`. Reference Agents table | no |

The agent paths in the reference's Agents table match the Go files cited above for every row that names a Go file. Crush, Copilot CLI, Cursor CLI, MiMo, and OpenCode are constructed in `agents.go`.

Six enabled agents share eight files with a magpie model pick: Codex `config.toml`, Pi `settings.json` and `models.json`, omp `config.yml` and `models.yml`, OpenCode `opencode.json`, Goose `config.yaml`, Grok `config.toml`. Claude Code and Hermes add two more paths that chezmoi deletes while those tools stay off.

### Who wins an apply

On a `modify_*` file, chezmoi's next apply writes its managed keys again. Where the template passes `replace`, the whole map is replaced: Codex `model_providers`, OpenCode `provider`, omp `modelRoles`. A `providers.magpie` entry inside that map does not survive.

Full templates are stricter. `home/dot_pi/private_agent/models.json.tmpl` and `home/dot_omp/private_agent/models.yml.tmpl` render the whole file from `llm/custom-providers`. The next apply deletes `providers.magpie` even if every other key was left alone.

Keys magpie sets that chezmoi does not manage survive apply:

- Codex `openai_base_url`. The Codex template never removes it. A signed-in magpie wiring would keep sending Codex at the gateway after apply restored `model` and `model_providers`.
- Grok `features.campaigns = false` and every `[model."magpie/…"]` table. Those tables contain `api_key`. `models.default` returns to the chezmoi Fast id. The gateway tables remain.
- `~/.config/goose/custom_providers/magpie.json`. The yaml keys `GOOSE_MODEL` and `GOOSE_PROVIDER` return to chezmoi. The extra file stays. That directory is absent today.
- Pi or omp `enabledModels` entries do not survive, because those keys are in the managed set.

Comments and unknown keys outside a replaced table survive a magpie edit. They do not survive a full-template render. They survive a modify apply only when they are not in `managed`, `replace`, or `remove`.

## What chezmoi owns that magpie does not model

- The OMP role table in `home/.chezmoidata/llm/omp.yaml`, rendered to `modelRoles`. Each role is an ordered candidate list: an IV alias first, a personal subscription second. `llm/pick-model` keeps the first alias whose provider resolved. Documented in `docs/llm/model-roles.md` and `docs/adr/0006-omp-model-role-tiers.md`.
- `host_env` gating of the `iv` provider set in `home/.chezmoidata/llm/common.yaml`. Off `iv`, the IV candidates disappear and the personal entry is what remains. Magpie profiles do not do this by themselves.
- Alias policy. `iv-codex`, `iv-cc`, `iv`, and `iv-anthropic` are the IV surfaces. Bundled `openai` and `anthropic` stay free for `/login`. One model id can exist on several providers, so this repo pins the provider. `docs/adr/0005-llm-provider-aliases.md`, `docs/adr/0010-iv-codex-iv-cc.md`.
- OMP models.dev overlays on the exact model id when `models: false`, and Pi's Cursor rates from `home/.chezmoidata/llm/cursor.yaml`. `docs/adr/0009-omp-models-dev-overlays.md`. Magpie's usage prices are a different table. They do not change what the agent is configured to call.
- Pi's unprefixed picker globs, OMP's provider-pinned globs, and the OpenRouter omission on pi, omp, and opencode.
- Request-time keys. Pi and OMP `apiKey` values are `!<pass-field command>` from `home/.chezmoitemplates/llm/custom-providers`. Codex uses `auth.command` with `bin/pass-field`. Magpie stores the key in `providers.json` and, for Grok Build, writes `api_key` into `config.toml`.
- MCP, plugins, keybindings, permissions, trust, status line, Goose extensions, and the Grok plugin marketplace. Those templates stay even if model keys were removed. The Library would write MCP, skills, and instructions again.
- Cursor CLI's 500k / high / fast parameter block, which magpie's Cursor adapter does not write, and does not write to the file the CLI reads on this machine.

## Install, and why the formula is the only shape that would fit

[magpie-releases README](https://github.com/yetone/magpie-releases/blob/main/README.md):

```sh
brew tap yetone/magpie-releases https://github.com/yetone/magpie-releases
brew install magpie
brew install --cask magpie-app
```

That README also shows `brew trust --tap yetone/magpie-releases`. This repo does not trust a tap wholesale. `home/.chezmoidata/packages/brew/taps.toml` uses `trusted.formula` or `trusted.cask` (see `achannarasappa/tap` / `ticker`, and `d12frosted/emacs-plus` / `emacs-plus-app`). A declaration would name `magpie` and, only if the app were wanted, `magpie-app`, in the same change as the package. The README says both update on every release, so `brew upgrade` sees them, and that the app also updates itself however it was installed. `magpie update` on a Homebrew CLI install tells you to run `brew upgrade magpie` instead. The cask's self-update fights brew. The formula is the shape that matches a chezmoi-managed binary on this Mac. The menu bar is optional. `curl | sh` and `go install` are upstream options and are not how this repo installs tools.

`yetone` and `magpie` are not in `taps.toml` today.

## What would have to move if magpie became the model layer

This is a replacement of `home/.chezmoidata/llm/` as the writer of model and provider blocks, not a `tools.yaml` entry.

1. Stop rendering model keys from the modify templates: Codex `model`, `model_provider`, `model_reasoning_effort`, `model_providers`, and `model_catalog_json`; Pi `defaultProvider`, `defaultModel`, `defaultThinkingLevel`, and `enabledModels`; omp `modelRoles` and `enabledModels`; OpenCode `model`, `small_model`, and `provider`; Goose `GOOSE_MODEL` and `GOOSE_PROVIDER`; Grok `models.default`. Leave MCP, plugins, themes, permissions, trust, and keybindings in those same files. The files stay `modify_*`. Magpie may edit only the keys it already edits. Chezmoi must not put those keys back.
2. Stop rendering `~/.pi/agent/models.json` and `~/.omp/agent/models.yml` as full files, or every apply deletes `providers.magpie`.
3. Move endpoints and tokens into magpie providers. Three IV tokens stay three providers. `pass` stops being the request-time key path for the agents magpie wires. Keys then live in `providers.json` (mode `0600`), and Grok's copy also lives in `config.toml`.
4. Replace each OMP role's candidate list with one magpie model. The `iv` / personal split becomes two profiles, switched by hand. Routing groups do not encode `host_env`, and they do not keep a different effort on the fallback.
5. Decide Cursor CLI separately. Magpie writes `~/.cursor/cli-config.json`. This machine's template says that file is not read. Magpie also does not write the 500k / fast parameter block.
6. Leave Claude Code, Hermes, and Gemini off, or stop purging those trees. With `purge_disabled_tools` on, apply deletes `~/.claude/**`, `~/.hermes/**`, and `~/.gemini/**`.
7. Do not turn the Library on against trees chezmoi still manages for MCP and skills.
8. Prove it in a scratch `HOME` before any apply against the real one.

Until that list is the intended change, magpie stays out of `tools.yaml` and out of `taps.toml`.

## Unverified

- The CLI syntax for a second API key on one provider. The README says each key can have its own proxy. The reference command found here, `magpie provider key`, replaces the key. The add-second-key command was not in the sections read.
- Whether Zed loads `config.json` as well as `settings.json`. The files are different paths. Both exist. Magpie's adapter opens only `settings.json`.
- Exact Library destination paths beyond "each agent's own MCP, skills, and instructions." `internal/library/mcp.go` was read only through the `Server` type. It was not traced per agent.
- The live contents of `~/.codex`, `~/.pi`, `~/.omp`, `~/.config/opencode`, `~/.config/goose`, `~/.grok`, and `~/.cursor`. Existence of a few paths was checked. Files were not read, and magpie was not executed.
- Homebrew formula and cask file names inside the tap repository. The releases README documents `brew install magpie` and `brew install --cask magpie-app`. A directory listing of that repo failed with a TLS error on this run, so the `.rb` filenames were not opened.
