# Design: OS Version Range in `os` `when` Condition

## Goal

Extend the `os` `when` condition so it can gate on the host's **OS version**
(semver constraint) in addition to the OS name, while keeping the existing
scalar (`os: darwin`) and list (`os: [darwin, linux]`) forms working unchanged.

## Data Source

Detect the OS version at config time in `home/.chezmoi.toml.tmpl` and store it
as `[data].os_version` (string), read by the `when` templates.

- darwin: `sw_vers -productVersion` (e.g. `26.5.2`)
- linux: `uname -r`, normalized by stripping from the first `-`
  (e.g. `6.5.0-27-generic` -> `6.5.0`)
- android: `getprop ro.build.version.release` (e.g. `14`)
- windows: `.chezmoi.windowsVersion` if non-empty, else `""`
- unknown / detection fails: `""`

`""` means "unknown".

## Condition Syntax

The `os` condition accepts three forms:

```yaml
when:
  enabled:
    os: darwin                          # scalar name match (existing)
    os: [darwin, linux]                 # list overlap (existing)
    os: {type: darwin, version: ">=14.0"}   # NEW: name + version constraint
```

Map form keys (both optional):
- `type`: OS name, scalar or list, matched against `.chezmoi.os` exactly as the
  existing scalar/list forms do.
- `version`: a semver constraint string (sprig `semverCompare` syntax, e.g.
  `">=14.0"`, `">=6.0 <7.0"`), compared against `os_version`.

## Empty-Version Handling

Lenient: when `os_version` is `""` (undetected), the `version` sub-check
**passes**. This also avoids `semverCompare` throwing on an empty version.

## Template Changes (`.chezmoitemplates/when/`)

- `when/semver` (new helper): input `dict "value" <string> "rule" <constraint>`;
  output JSON bool. `value == ""` -> `true`; else `semverCompare rule value`.
- `when/check`: for key `os`, when the rule (under `enabled`/`disabled`) is a
  **map**, evaluate `type` via `when/match` (against `.value`, the OS name) and
  `version` via `when/semver` (against a separately supplied `os_version`);
  both must pass. When the rule is scalar/list, keep existing `when/match`
  behavior. `when/check` gains an optional `os_version` input used only for this
  key.
- `when/context`: the existing `os` check passes `os_version`
  (via `dig "os_version" "" .`) into `when/check` so the map form can see it.

Numeric (`mem_gb`/`disk_gb`) and other conditions are untouched.

## Testing / Verification

- `chezmoi execute-template` for `when/semver`: empty->true, in-range->true,
  out-of-range->false, range constraint.
- `when/check` for `os`: scalar (existing), list (existing), map type-only,
  map version-only, map type+version pass/fail, disabled map.
- `when/context`: map form gated live against this host
  (darwin `26.5.2`).
- `chezmoi init` + `chezmoi data` shows `os_version`.
- `chezmoi apply --dry-run` clean; existing skill/MCP resolution unaffected.

## Out of Scope

- Changing numeric capacity conditions.
- Non-`os` version conditions.
- Windows-native version detection beyond `.chezmoi.windowsVersion`.
