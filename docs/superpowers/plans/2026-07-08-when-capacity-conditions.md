# Memory & Storage Capacity `when` Conditions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let items (skills, MCP providers) gate on host physical memory (`mem_gb`) and system storage capacity (`disk_gb`) via `when.enabled`/`when.disabled` min/max thresholds.

**Architecture:** Detect capacities per-OS at config time in `.chezmoi.toml.tmpl` and expose them as numeric `[data]` fields. Add a `when/range` helper for numeric min/max matching, route map-with-min/max rules to it from `when/check`, and add `mem_gb`/`disk_gb` checks to `when/context`. Existing exact-match/overlap conditions are untouched.

**Tech Stack:** chezmoi Go text/template + sprig, POSIX `sh`/`sysctl`/`df`/`awk`.

## Global Constraints

- Units: whole GB, field names `mem_gb` and `disk_gb`.
- `disk_gb` = total capacity of root filesystem `/`, not free space.
- Detection failure / unsupported OS (windows, unknown) yields `0`.
- `0` means "unknown" and numeric conditions **pass** leniently on `0`.
- Threshold rule form: map with optional `min` and/or `max` keys.
- Do not change semantics of existing `device_type`/`host_env`/`os`/`roles` conditions.
- Verify with `chezmoi execute-template`; this host is darwin/arm64 with `mem_gb=24`, `disk_gb≈926`.

---

### Task 1: `when/range` numeric matcher helper

**Files:**
- Create: `home/.chezmoitemplates/when/range`

**Interfaces:**
- Consumes: nothing.
- Produces: template `when/range`, input `dict "value" <int> "rule" <map with optional min/max>`, output JSON bool. `value == 0` -> `true` (lenient). Missing bound = unbounded on that side.

- [ ] **Step 1: Write the helper template**

Create `home/.chezmoitemplates/when/range`:

```
{{- /* Numeric range match for capacity conditions.
       Input:  dict "value" <int> "rule" <map with optional min/max>
       Output: JSON boolean
       - value == 0 means "unknown" -> pass (lenient)
       - {min: N}        -> value >= N
       - {max: N}        -> value <= N
       - {min: A, max: B}-> A <= value <= B
       - missing bound   -> unbounded on that side */ -}}
{{- $value := .value -}}
{{- $rule := .rule -}}
{{- $result := true -}}
{{- if eq $value 0 -}}
  {{- $result = true -}}
{{- else -}}
  {{- if hasKey $rule "min" -}}
    {{- if lt $value (index $rule "min") }}{{- $result = false -}}{{- end -}}
  {{- end -}}
  {{- if and $result (hasKey $rule "max") -}}
    {{- if gt $value (index $rule "max") }}{{- $result = false -}}{{- end -}}
  {{- end -}}
{{- end -}}
{{- toJson $result -}}
```

- [ ] **Step 2: Verify pass/fail cases**

Run:
```bash
cd ~/.local/share/chezmoi
for t in \
  '{{ includeTemplate "when/range" (dict "value" 24 "rule" (dict "min" 16)) }}' \
  '{{ includeTemplate "when/range" (dict "value" 8  "rule" (dict "min" 16)) }}' \
  '{{ includeTemplate "when/range" (dict "value" 24 "rule" (dict "max" 16)) }}' \
  '{{ includeTemplate "when/range" (dict "value" 24 "rule" (dict "min" 16 "max" 64)) }}' \
  '{{ includeTemplate "when/range" (dict "value" 100 "rule" (dict "min" 16 "max" 64)) }}' \
  '{{ includeTemplate "when/range" (dict "value" 0  "rule" (dict "min" 16)) }}' ; do
  chezmoi execute-template "$t"; echo
done
```
Expected (one per line): `true`, `false`, `false`, `true`, `false`, `true`

- [ ] **Step 3: Commit**

```bash
cd ~/.local/share/chezmoi
git add home/.chezmoitemplates/when/range
git commit -m "feat(when): add numeric range matcher for capacity conditions"
```

---

### Task 2: Route range rules in `when/check`

**Files:**
- Modify: `home/.chezmoitemplates/when/check`

**Interfaces:**
- Consumes: `when/range` (Task 1), existing `when/match`.
- Produces: `when/check` unchanged signature; when a rule (under `enabled`/`disabled` for the given key) is a map containing `min` or `max`, it delegates to `when/range`; otherwise `when/match`.

- [ ] **Step 1: Update the enabled branch**

In `home/.chezmoitemplates/when/check`, replace the enabled-map block:

```
    {{- else if and (eq (kindOf $when.enabled) "map") (hasKey $when.enabled $key) -}}
      {{- $expected := index $when.enabled $key -}}
      {{- if not (includeTemplate "when/match" (dict "value" $value "rule" $expected) | fromJson) }}{{- $result = false -}}{{- end -}}
    {{- end -}}
```

with:

```
    {{- else if and (eq (kindOf $when.enabled) "map") (hasKey $when.enabled $key) -}}
      {{- $expected := index $when.enabled $key -}}
      {{- if and (eq (kindOf $expected) "map") (or (hasKey $expected "min") (hasKey $expected "max")) -}}
        {{- if not (includeTemplate "when/range" (dict "value" $value "rule" $expected) | fromJson) }}{{- $result = false -}}{{- end -}}
      {{- else -}}
        {{- if not (includeTemplate "when/match" (dict "value" $value "rule" $expected) | fromJson) }}{{- $result = false -}}{{- end -}}
      {{- end -}}
    {{- end -}}
```

- [ ] **Step 2: Update the disabled branch**

Replace the disabled-map block:

```
    {{- else if and (eq (kindOf $disabledValue) "map") (hasKey $disabledValue $key) -}}
      {{- $blocked := index $disabledValue $key -}}
      {{- if includeTemplate "when/match" (dict "value" $value "rule" $blocked) | fromJson }}{{- $result = false -}}{{- end -}}
    {{- end -}}
```

with:

```
    {{- else if and (eq (kindOf $disabledValue) "map") (hasKey $disabledValue $key) -}}
      {{- $blocked := index $disabledValue $key -}}
      {{- if and (eq (kindOf $blocked) "map") (or (hasKey $blocked "min") (hasKey $blocked "max")) -}}
        {{- if includeTemplate "when/range" (dict "value" $value "rule" $blocked) | fromJson }}{{- $result = false -}}{{- end -}}
      {{- else -}}
        {{- if includeTemplate "when/match" (dict "value" $value "rule" $blocked) | fromJson }}{{- $result = false -}}{{- end -}}
      {{- end -}}
    {{- end -}}
```

- [ ] **Step 3: Verify numeric routing + no regression on existing rules**

Run:
```bash
cd ~/.local/share/chezmoi
# numeric enabled: value 24, min 16 -> true
chezmoi execute-template '{{ includeTemplate "when/check" (dict "item" (dict "when" (dict "enabled" (dict "mem_gb" (dict "min" 16)))) "key" "mem_gb" "value" 24) }}'; echo
# numeric enabled: value 8, min 16 -> false
chezmoi execute-template '{{ includeTemplate "when/check" (dict "item" (dict "when" (dict "enabled" (dict "mem_gb" (dict "min" 16)))) "key" "mem_gb" "value" 8) }}'; echo
# numeric disabled: value 24, max 4 blocked? in range<=4 false -> not blocked -> true
chezmoi execute-template '{{ includeTemplate "when/check" (dict "item" (dict "when" (dict "disabled" (dict "disk_gb" (dict "max" 4)))) "key" "disk_gb" "value" 24) }}'; echo
# existing scalar rule still works: device_type laptop matches laptop -> true
chezmoi execute-template '{{ includeTemplate "when/check" (dict "item" (dict "when" (dict "enabled" (dict "device_type" "laptop"))) "key" "device_type" "value" "laptop") }}'; echo
# existing list rule: roles overlap -> true
chezmoi execute-template '{{ includeTemplate "when/check" (dict "item" (dict "when" (dict "enabled" (dict "roles" (list "llm" "work")))) "key" "roles" "value" (list "work")) }}'; echo
```
Expected (one per line): `true`, `false`, `true`, `true`, `true`

- [ ] **Step 4: Commit**

```bash
cd ~/.local/share/chezmoi
git add home/.chezmoitemplates/when/check
git commit -m "feat(when): route min/max rules to numeric range matcher"
```

---

### Task 3: Add capacity checks to `when/context`

**Files:**
- Modify: `home/.chezmoitemplates/when/context`

**Interfaces:**
- Consumes: `when/check` (Task 2). Reads `.mem_gb` / `.disk_gb` from root context (provided by Task 4).
- Produces: `when/context` now ANDs in `mem_gb` and `disk_gb` checks.

- [ ] **Step 1: Add the two checks**

In `home/.chezmoitemplates/when/context`, after the `$rolesOk` line and before the final `toJson`, add:

```
{{- $memOk := includeTemplate "when/check" (dict "item" .item "key" "mem_gb" "value" (.mem_gb | default 0)) | fromJson -}}
{{- $diskOk := includeTemplate "when/check" (dict "item" .item "key" "disk_gb" "value" (.disk_gb | default 0)) | fromJson -}}
```

and change the final line from:

```
{{- toJson (and $hostEnvOk $deviceTypeOk $osOk $rolesOk) -}}
```

to:

```
{{- toJson (and $hostEnvOk $deviceTypeOk $osOk $rolesOk $memOk $diskOk) -}}
```

- [ ] **Step 2: Verify context gating**

Run:
```bash
cd ~/.local/share/chezmoi
# item requiring mem>=16 on a host with mem_gb=24 -> true
chezmoi execute-template '{{ includeTemplate "when/context" (dict "item" (dict "when" (dict "enabled" (dict "mem_gb" (dict "min" 16)))) "mem_gb" 24 "disk_gb" 926 "device_type" "laptop" "host_env" "iv" "roles" (list "work") "chezmoi" (dict "os" "darwin")) }}'; echo
# item requiring mem>=64 -> false
chezmoi execute-template '{{ includeTemplate "when/context" (dict "item" (dict "when" (dict "enabled" (dict "mem_gb" (dict "min" 64)))) "mem_gb" 24 "disk_gb" 926 "device_type" "laptop" "host_env" "iv" "roles" (list "work") "chezmoi" (dict "os" "darwin")) }}'; echo
# item with no capacity condition -> true (backward compatible)
chezmoi execute-template '{{ includeTemplate "when/context" (dict "item" (dict) "mem_gb" 24 "disk_gb" 926 "device_type" "laptop" "host_env" "iv" "roles" (list "work") "chezmoi" (dict "os" "darwin")) }}'; echo
# missing mem_gb in context (default 0) with mem>=16 rule -> lenient true
chezmoi execute-template '{{ includeTemplate "when/context" (dict "item" (dict "when" (dict "enabled" (dict "mem_gb" (dict "min" 16)))) "device_type" "laptop" "host_env" "iv" "roles" (list "work") "chezmoi" (dict "os" "darwin")) }}'; echo
```
Expected (one per line): `true`, `false`, `true`, `true`

- [ ] **Step 3: Commit**

```bash
cd ~/.local/share/chezmoi
git add home/.chezmoitemplates/when/context
git commit -m "feat(when): gate items on mem_gb and disk_gb"
```

---

### Task 4: Detect and expose `mem_gb`/`disk_gb` in config data

**Files:**
- Modify: `home/.chezmoi.toml.tmpl`

**Interfaces:**
- Consumes: nothing.
- Produces: `[data].mem_gb` and `[data].disk_gb` as integers, readable as `.mem_gb` / `.disk_gb` in all templates.

- [ ] **Step 1: Compute the values**

In `home/.chezmoi.toml.tmpl`, after the `{{- $os := .chezmoi.os -}}` line (currently line 23), add:

```
{{- $memGb := 0 -}}
{{- $diskGb := 0 -}}
{{- if eq $os "darwin" -}}
  {{- $memGb = atoi (output "sh" "-c" "echo $(( $(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1073741824 ))" | trim) -}}
{{- else if or (eq $os "linux") (eq $os "android") -}}
  {{- $memGb = atoi (output "sh" "-c" "awk '/MemTotal/{printf \"%d\", int($2/1048576)}' /proc/meminfo 2>/dev/null || echo 0" | trim) -}}
{{- end -}}
{{- if or (eq $os "darwin") (eq $os "linux") (eq $os "android") -}}
  {{- $diskGb = atoi (output "sh" "-c" "df -k / 2>/dev/null | awk 'NR==2{printf \"%d\", int($2/1048576)}' || echo 0" | trim) -}}
{{- end -}}
```

- [ ] **Step 2: Emit the data fields**

In the `[data]` block, after the `isDarkMode` line, add:

```
    mem_gb = {{ $memGb }}
    disk_gb = {{ $diskGb }}
```

- [ ] **Step 3: Verify config renders with correct values**

Run:
```bash
cd ~/.local/share/chezmoi
chezmoi execute-template --init --promptString email=x < home/.chezmoi.toml.tmpl 2>/dev/null | grep -E 'mem_gb|disk_gb'
```
Expected: `mem_gb = 24` and `disk_gb = 926` (darwin/arm64 host).

If the above prompt form errors, alternatively verify the fragment directly:
```bash
chezmoi execute-template '{{ atoi (output "sh" "-c" "echo $(( $(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1073741824 ))" | trim) }}'; echo
chezmoi execute-template '{{ atoi (output "sh" "-c" "df -k / 2>/dev/null | awk (printf) || echo 0" | trim) }}' 2>/dev/null || echo "use fragment from Step 1 verbatim"
```
Expected: `24` for memory.

- [ ] **Step 4: Regenerate config and confirm live data**

Run:
```bash
cd ~/.local/share/chezmoi
chezmoi init
chezmoi data --format=json | grep -E '"mem_gb"|"disk_gb"'
```
Expected: `"mem_gb": 24` and `"disk_gb": 926`.

- [ ] **Step 5: Commit**

```bash
cd ~/.local/share/chezmoi
git add home/.chezmoi.toml.tmpl
git commit -m "feat(chezmoi): detect mem_gb and disk_gb capacity data"
```

---

### Task 5: End-to-end verification against real skills/MCP resolution

**Files:**
- No code changes (verification only).

**Interfaces:**
- Consumes: all prior tasks.
- Produces: confidence that skill/MCP resolution is unaffected and capacity gating works live.

- [ ] **Step 1: Confirm existing skill resolution unchanged**

Run:
```bash
cd ~/.local/share/chezmoi
chezmoi cat home/.chezmoiscripts/run_onchange_after_200_setup-skills.sh.tmpl 2>&1 | head -40
```
Expected: renders without template errors; agent lists resolve as before.

- [ ] **Step 2: Live capacity-gated resolution smoke test**

Run (uses live `.mem_gb`):
```bash
cd ~/.local/share/chezmoi
chezmoi execute-template '{{ includeTemplate "when/context" (merge (dict "item" (dict "when" (dict "enabled" (dict "mem_gb" (dict "min" 16))))) .) }}'; echo
chezmoi execute-template '{{ includeTemplate "when/context" (merge (dict "item" (dict "when" (dict "enabled" (dict "mem_gb" (dict "min" 999))))) .) }}'; echo
```
Expected: `true` then `false` (this host has 24 GB).

- [ ] **Step 3: Dry-run apply to confirm no unintended changes**

Run:
```bash
cd ~/.local/share/chezmoi
chezmoi apply --dry-run --verbose 2>&1 | head -40
```
Expected: no template errors; only the config-data change (if any) shows, no unrelated churn.

- [ ] **Step 4: Commit (if any docs/notes updated)**

```bash
cd ~/.local/share/chezmoi
git add -A
git commit -m "test: verify capacity when-conditions end-to-end" --allow-empty
```

---

## Self-Review

**Spec coverage:**
- Data source A (config-time detection, `[data]` numeric fields) -> Task 4.
- `mem_gb`/`disk_gb` per-OS detection incl. `0` fallback -> Task 4 Step 1.
- min/max threshold syntax -> Task 1 (`when/range`).
- Lenient `0` handling -> Task 1 Step 1 (`eq $value 0` -> true).
- context integration -> Task 3.
- routing without breaking existing conditions -> Task 2.
- verification via `execute-template` + dry-run -> Tasks 1-5.
All spec sections covered.

**Placeholder scan:** No TBD/TODO; every code step shows full content. (Task 4 Step 3 alternate command is a fallback note, primary command is complete.)

**Type consistency:** `when/range` input `value:int, rule:map` matches how Task 2 calls it and Task 3 supplies `value` via `.mem_gb|default 0` (int). `mem_gb`/`disk_gb` are ints in toml (Task 4) and compared with int bounds. Consistent throughout.
