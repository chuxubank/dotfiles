# Chezmoi config management

Source of truth for one user's machines: declare intent in data files, resolve it through templates, write destination files and run install scripts.

`.chezmoidata` → resolver templates → source targets/scripts → destination

## Pipeline

1. **Data** in `home/.chezmoidata/` names tools, packages, skills, services, policies, and pinned installers.
2. **Resolver templates** in `home/.chezmoitemplates/` turn that data plus host facts into booleans, lists, and merged documents. Callers should not reimplement `when/*`, `tool/*`, or `package/items`.
3. **Source targets and scripts** under `home/` consume those resolvers. One destination path has one writer.
4. **Destination** is the live home directory. `modify_` files merge through `config/merge`. `.chezmoiremove` deletes dest paths for disabled tools.

Local and CI verification is the same command: `make verify`.

## Invariants

**One writer per path.** A destination file is owned by one source target (or one modify-template). Do not add a second template, script, or external that writes the same path.

**Modify-template merge.** Files named `modify_*` keep unmanaged keys. They call `config/merge` with a format, the existing document, and the managed map. Use `replace` / `remove` only for keys this repo must own.

**Tool lifecycle.** A name in `tools.yaml` is the enablement switch. Packages, skill providers, and defaults affiliate with `owner`. Services and environment groups use `tool` as identity and set `owner` only when they should follow the switch. `when.*.tool` on skills/mcp/plugins is the target agent, not the owner. Every `owner` must be declared.

**Destructive operations.** `remove` deletes chezmoi-managed dest files when a tool is off. `purge` deletes runtime data and is off unless `policies.purge_disabled_tools` is on. `policies.uninstall_microsoft_edge` is the Edge zap switch. Open-world package uninstall (uv/bun/sdkman/cargo) still removes undeclared inventory names; that is reconcile, not purge.

**Remote execution.** Bootstrap installers in `installers.yaml` are version-pinned and SHA256-checked. `./install.sh --plan` and `make plan` only print a dry-run. Personal git sources (skills, some plugins) may follow a branch.

## Language

**Owner**:
The declared lifecycle switch a package, skill provider, default, service, or environment group follows.
_Avoid_: tool (except as identity or target agent)

**Tool**:
A name in `tools.yaml`, or the identity of a service/environment group, or the target agent for skills/mcp/plugins.
_Avoid_: using this field for lifecycle affiliation (use owner)

**Remove**:
Deletion of chezmoi-managed destination files when a tool is off.
_Avoid_: uninstall, clean, zap

**Purge**:
Deletion of a tool's runtime data (login state, history, caches), opt-in via policy.
_Avoid_: remove, uninstall

**Policy**:
A named, explicit switch for a destructive or host-wide action (`purge_disabled_tools`, `uninstall_microsoft_edge`).
_Avoid_: implied by host_env alone

**When**:
The shared condition object (`enabled` / `disabled`) evaluated by `when/evaluate`.
_Avoid_: if, gate, match (except `when/match`)

**Resolver**:
A template whose interface is a JSON value (boolean, list, or document) consumed by many callers.
_Avoid_: helper, partial, macro
