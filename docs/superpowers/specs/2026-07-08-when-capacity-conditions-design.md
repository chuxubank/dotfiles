# Design: Memory & Storage Capacity `when` Conditions

## Goal

Extend the `.chezmoitemplates/when/` condition system so items (skills, MCP
providers) can be gated on the host's **physical memory** and **system storage
capacity**, in addition to the existing `device_type` / `host_env` / `os` /
`roles` conditions.

## Data Source

Detect capacities at config time in `home/.chezmoi.toml.tmpl` and store them as
numeric fields in `[data]`, so the `when` templates read them exactly like the
other context values.

- `mem_gb` — total physical RAM, rounded to whole GB
  - darwin: `sysctl -n hw.memsize` (bytes) / 1024^3
  - linux: `MemTotal` from `/proc/meminfo` (kB) / 1024^2
  - android: same as linux (`/proc/meminfo`)
  - windows / unknown: `0`
- `disk_gb` — total capacity of the root/system filesystem, rounded to whole GB
  - darwin / linux / android: `df -k /` total 1K-blocks / 1024^2
  - windows / unknown: `0`

Every detection command is wrapped so failure yields `0`. `0` means "unknown".

## Condition Syntax

Numeric thresholds use optional `min`/`max` bounds (map form):

```yaml
when:
  enabled:
    mem_gb: {min: 16}            # actual >= 16
    disk_gb: {min: 100, max: 2000}  # 100 <= actual <= 2000
```

- `{min: N}` -> pass when `value >= N`
- `{max: N}` -> pass when `value <= N`
- `{min: A, max: B}` -> pass when `A <= value <= B`
- both bounds optional

## `0` (unknown) Handling

Lenient: when the detected value is `0` (detection unavailable, e.g. Windows),
the numeric condition **passes**. Rationale: don't hide capability-gated items
on hosts we simply couldn't measure.

## Template Changes (`.chezmoitemplates/when/`)

- `when/context`: add `mem_gb` and `disk_gb` checks alongside the existing four,
  passing `.mem_gb` / `.disk_gb` as the context value.
- `when/range` (new helper): given `dict "value" V "rule" R` where `R` is a map
  with optional `min`/`max`, return JSON bool per the semantics above; `V == 0`
  returns `true` (lenient).
- `when/check`: when the expected/blocked rule for a key is a **map** containing
  `min` or `max`, route to `when/range` (numeric). Otherwise fall back to the
  existing `when/match` (equality / overlap). This keeps all current conditions
  unchanged.
  - `enabled` numeric rule passes -> stays enabled; fails -> disabled.
  - `disabled` numeric rule matches (in range) -> disabled.

## Testing / Verification

- `chezmoi execute-template` on the modified `.chezmoi.toml.tmpl` to confirm
  `mem_gb` / `disk_gb` resolve to sane whole numbers on this host (darwin).
- Exercise `when/range` and `when/check` with representative dicts via
  `chezmoi execute-template` (min-only, max-only, both, out-of-range, and
  `value == 0`), asserting expected JSON booleans.
- `chezmoi apply --dry-run` (or diff) to confirm existing skill/MCP resolution
  is unaffected.

## Out of Scope

- Free/available disk space (only total capacity).
- CPU / core-count or other hardware conditions.
- Windows-native detection (returns `0` -> lenient pass).
