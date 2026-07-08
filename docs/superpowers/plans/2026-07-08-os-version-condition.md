# OS Version Range `when` Condition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the `os` `when` condition gate on an OS version semver constraint via a map form `os: {type: <name>, version: <constraint>}`, keeping scalar/list forms unchanged.

**Architecture:** Detect `os_version` per-OS at config time into `[data]`. Add a `when/semver` matcher (lenient on empty). In `when/check`, when the `os` rule is a map, match `type` via `when/match` and `version` via `when/semver` (using an extra `os_version` input); scalar/list `os` rules keep existing behavior. `when/context` feeds `os_version` into the `os` check.

**Tech Stack:** chezmoi Go text/template + sprig (`semverCompare`, `splitList`, `dig`), POSIX `sh`/`sw_vers`/`uname`/`getprop`.

## Global Constraints

- New data field: `os_version` (string).
- linux version normalized: strip from first `-` (`6.5.0-27-generic` -> `6.5.0`).
- Detection failure / unsupported yields `""`.
- `""` version => `version` sub-check **passes** (lenient) and must short-circuit before `semverCompare` (which throws on empty).
- `os` map keys `type` (scalar or list, name match) and `version` (semver constraint); both optional.
- Preserve existing scalar/list `os` behavior and all other conditions (`device_type`/`host_env`/`roles`/`mem_gb`/`disk_gb`).
- Verify with `chezmoi execute-template`; this host is darwin, `os_version=26.5.2`.

---

### Task 1: `when/semver` matcher helper

**Files:**
- Create: `home/.chezmoitemplates/when/semver`

**Interfaces:**
- Consumes: nothing.
- Produces: template `when/semver`, input `dict "value" <string> "rule" <constraint string>`, output JSON bool. `value == ""` -> `true`; else `semverCompare rule value`.

- [ ] **Step 1: Write the helper template**

Create `home/.chezmoitemplates/when/semver`:

```
{{- /* Semver constraint match for os version conditions.
       Input:  dict "value" <version string> "rule" <semverCompare constraint>
       Output: JSON boolean
       - value == "" means "unknown" -> pass (lenient; also avoids throw) */ -}}
{{- $value := .value -}}
{{- $rule := .rule -}}
{{- $result := true -}}
{{- if ne $value "" -}}
  {{- $result = semverCompare $rule $value -}}
{{- end -}}
{{- toJson $result -}}
```

- [ ] **Step 2: Verify cases**

Run:
```bash
cd ~/.local/share/chezmoi
for t in \
  '{{ includeTemplate "when/semver" (dict "value" "26.5.2" "rule" ">=14.0") }}' \
  '{{ includeTemplate "when/semver" (dict "value" "13.0"   "rule" ">=14.0") }}' \
  '{{ includeTemplate "when/semver" (dict "value" "6.5.0"  "rule" ">=6.0 <7.0") }}' \
  '{{ includeTemplate "when/semver" (dict "value" "7.1.0"  "rule" ">=6.0 <7.0") }}' \
  '{{ includeTemplate "when/semver" (dict "value" ""       "rule" ">=14.0") }}' ; do
  chezmoi execute-template "$t"; echo
done
```
Expected (one per line): `true`, `false`, `true`, `false`, `true`

- [ ] **Step 3: Commit**

```bash
cd ~/.local/share/chezmoi
git add home/.chezmoitemplates/when/semver
git commit -m "feat(when): add semver matcher for os version conditions"
```

---

### Task 2: Route `os` map rules in `when/check`

**Files:**
- Modify: `home/.chezmoitemplates/when/check`

**Interfaces:**
- Consumes: `when/semver` (Task 1), existing `when/match`.
- Produces: `when/check` gains optional `os_version` input. For key `os` with a map rule, evaluates `type` (via `when/match` against `.value`) AND `version` (via `when/semver` against `os_version`). Scalar/list `os` rules and all other keys unchanged.

- [ ] **Step 1: Read the current enabled/disabled map blocks**

Run:
```bash
cd ~/.local/share/chezmoi
cat home/.chezmoitemplates/when/check
```
Note the current structure: after Task 2 of the capacity plan, the enabled and disabled branches each route map-with-min/max to `when/range`, else `when/match`.

- [ ] **Step 2: Add os-map handling to the enabled branch**

In `home/.chezmoitemplates/when/check`, the enabled map branch currently reads:

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

Replace it with (adds an `os`-map case before the min/max case):

```
    {{- else if and (eq (kindOf $when.enabled) "map") (hasKey $when.enabled $key) -}}
      {{- $expected := index $when.enabled $key -}}
      {{- if and (eq $key "os") (eq (kindOf $expected) "map") -}}
        {{- if hasKey $expected "type" -}}
          {{- if not (includeTemplate "when/match" (dict "value" $value "rule" (index $expected "type")) | fromJson) }}{{- $result = false -}}{{- end -}}
        {{- end -}}
        {{- if and $result (hasKey $expected "version") -}}
          {{- if not (includeTemplate "when/semver" (dict "value" (.os_version | default "") "rule" (index $expected "version")) | fromJson) }}{{- $result = false -}}{{- end -}}
        {{- end -}}
      {{- else if and (eq (kindOf $expected) "map") (or (hasKey $expected "min") (hasKey $expected "max")) -}}
        {{- if not (includeTemplate "when/range" (dict "value" $value "rule" $expected) | fromJson) }}{{- $result = false -}}{{- end -}}
      {{- else -}}
        {{- if not (includeTemplate "when/match" (dict "value" $value "rule" $expected) | fromJson) }}{{- $result = false -}}{{- end -}}
      {{- end -}}
    {{- end -}}
```

Note: `.os_version` here refers to the `when/check` input dict; it is supplied by `when/context` in Task 3. `default ""` keeps it safe when absent.

- [ ] **Step 3: Add os-map handling to the disabled branch**

The disabled map branch currently reads:

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

Replace it with (adds `os`-map case; disabled means "blocked when it matches", so the map matches only when BOTH provided sub-conditions match):

```
    {{- else if and (eq (kindOf $disabledValue) "map") (hasKey $disabledValue $key) -}}
      {{- $blocked := index $disabledValue $key -}}
      {{- if and (eq $key "os") (eq (kindOf $blocked) "map") -}}
        {{- $osMatch := true -}}
        {{- if hasKey $blocked "type" -}}
          {{- if not (includeTemplate "when/match" (dict "value" $value "rule" (index $blocked "type")) | fromJson) }}{{- $osMatch = false -}}{{- end -}}
        {{- end -}}
        {{- if and $osMatch (hasKey $blocked "version") -}}
          {{- if not (includeTemplate "when/semver" (dict "value" (.os_version | default "") "rule" (index $blocked "version")) | fromJson) }}{{- $osMatch = false -}}{{- end -}}
        {{- end -}}
        {{- if $osMatch }}{{- $result = false -}}{{- end -}}
      {{- else if and (eq (kindOf $blocked) "map") (or (hasKey $blocked "min") (hasKey $blocked "max")) -}}
        {{- if includeTemplate "when/range" (dict "value" $value "rule" $blocked) | fromJson }}{{- $result = false -}}{{- end -}}
      {{- else -}}
        {{- if includeTemplate "when/match" (dict "value" $value "rule" $blocked) | fromJson }}{{- $result = false -}}{{- end -}}
      {{- end -}}
    {{- end -}}
```

- [ ] **Step 4: Verify os routing + no regression**

Run:
```bash
cd ~/.local/share/chezmoi
# scalar os (existing): darwin==darwin -> true
chezmoi execute-template '{{ includeTemplate "when/check" (dict "item" (dict "when" (dict "enabled" (dict "os" "darwin"))) "key" "os" "value" "darwin") }}'; echo
# list os (existing): darwin in [darwin linux] -> true
chezmoi execute-template '{{ includeTemplate "when/check" (dict "item" (dict "when" (dict "enabled" (dict "os" (list "darwin" "linux")))) "key" "os" "value" "darwin") }}'; echo
# map type-only match -> true
chezmoi execute-template '{{ includeTemplate "when/check" (dict "item" (dict "when" (dict "enabled" (dict "os" (dict "type" "darwin")))) "key" "os" "value" "darwin") }}'; echo
# map type mismatch -> false
chezmoi execute-template '{{ includeTemplate "when/check" (dict "item" (dict "when" (dict "enabled" (dict "os" (dict "type" "linux")))) "key" "os" "value" "darwin") }}'; echo
# map type+version pass: darwin + >=14 with os_version 26.5.2 -> true
chezmoi execute-template '{{ includeTemplate "when/check" (dict "item" (dict "when" (dict "enabled" (dict "os" (dict "type" "darwin" "version" ">=14.0")))) "key" "os" "value" "darwin" "os_version" "26.5.2") }}'; echo
# map version fail: >=99 -> false
chezmoi execute-template '{{ includeTemplate "when/check" (dict "item" (dict "when" (dict "enabled" (dict "os" (dict "type" "darwin" "version" ">=99.0")))) "key" "os" "value" "darwin" "os_version" "26.5.2") }}'; echo
# map version-only, empty os_version -> lenient true
chezmoi execute-template '{{ includeTemplate "when/check" (dict "item" (dict "when" (dict "enabled" (dict "os" (dict "version" ">=99.0")))) "key" "os" "value" "darwin") }}'; echo
# disabled map matches (darwin + >=14) -> blocked -> false
chezmoi execute-template '{{ includeTemplate "when/check" (dict "item" (dict "when" (dict "disabled" (dict "os" (dict "type" "darwin" "version" ">=14.0")))) "key" "os" "value" "darwin" "os_version" "26.5.2") }}'; echo
```
Expected (one per line): `true`, `true`, `true`, `false`, `true`, `false`, `true`, `false`

- [ ] **Step 5: Commit**

```bash
cd ~/.local/share/chezmoi
git add home/.chezmoitemplates/when/check
git commit -m "feat(when): support os map form with version constraint"
```

---

### Task 3: Pass `os_version` into the `os` check in `when/context`

**Files:**
- Modify: `home/.chezmoitemplates/when/context`

**Interfaces:**
- Consumes: `when/check` (Task 2). Reads `.os_version` from root context (Task 4).
- Produces: the existing `os` check now also passes `os_version`.

- [ ] **Step 1: Update the os check line**

In `home/.chezmoitemplates/when/context`, the current line:

```
{{- $osOk := includeTemplate "when/check" (dict "item" .item "key" "os" "value" .chezmoi.os) | fromJson -}}
```

Replace with:

```
{{- $osOk := includeTemplate "when/check" (dict "item" .item "key" "os" "value" .chezmoi.os "os_version" (dig "os_version" "" .)) | fromJson -}}
```

- [ ] **Step 2: Verify context gating**

Run:
```bash
cd ~/.local/share/chezmoi
# darwin + >=14 with os_version present -> true
chezmoi execute-template '{{ includeTemplate "when/context" (dict "item" (dict "when" (dict "enabled" (dict "os" (dict "type" "darwin" "version" ">=14.0")))) "os_version" "26.5.2" "device_type" "laptop" "host_env" "iv" "roles" (list "work") "chezmoi" (dict "os" "darwin")) }}'; echo
# darwin + >=99 -> false
chezmoi execute-template '{{ includeTemplate "when/context" (dict "item" (dict "when" (dict "enabled" (dict "os" (dict "type" "darwin" "version" ">=99.0")))) "os_version" "26.5.2" "device_type" "laptop" "host_env" "iv" "roles" (list "work") "chezmoi" (dict "os" "darwin")) }}'; echo
# missing os_version in context, version rule -> lenient true
chezmoi execute-template '{{ includeTemplate "when/context" (dict "item" (dict "when" (dict "enabled" (dict "os" (dict "type" "darwin" "version" ">=99.0")))) "device_type" "laptop" "host_env" "iv" "roles" (list "work") "chezmoi" (dict "os" "darwin")) }}'; echo
# scalar os still works -> true
chezmoi execute-template '{{ includeTemplate "when/context" (dict "item" (dict "when" (dict "enabled" (dict "os" "darwin"))) "os_version" "26.5.2" "device_type" "laptop" "host_env" "iv" "roles" (list "work") "chezmoi" (dict "os" "darwin")) }}'; echo
```
Expected (one per line): `true`, `false`, `true`, `true`

- [ ] **Step 3: Commit**

```bash
cd ~/.local/share/chezmoi
git add home/.chezmoitemplates/when/context
git commit -m "feat(when): feed os_version into os condition check"
```

---

### Task 4: Detect and expose `os_version` in config data

**Files:**
- Modify: `home/.chezmoi.toml.tmpl`

**Interfaces:**
- Consumes: nothing.
- Produces: `[data].os_version` (string), readable as `.os_version`.

- [ ] **Step 1: Compute the value**

In `home/.chezmoi.toml.tmpl`, after the `$diskGb` detection block added by the capacity plan (right before `{{- if $interactive }}`), add:

```
{{- $osVersion := "" -}}
{{- if eq $os "darwin" -}}
  {{- $osVersion = output "sh" "-c" "sw_vers -productVersion 2>/dev/null || echo" | trim -}}
{{- else if eq $os "linux" -}}
  {{- $osVersion = (splitList "-" (output "sh" "-c" "uname -r 2>/dev/null || echo" | trim)) | first -}}
{{- else if eq $os "android" -}}
  {{- $osVersion = output "sh" "-c" "getprop ro.build.version.release 2>/dev/null || echo" | trim -}}
{{- else if eq $os "windows" -}}
  {{- $osVersion = .chezmoi.windowsVersion | default "" -}}
{{- end -}}
```

- [ ] **Step 2: Emit the data field**

In the `[data]` block, after the `disk_gb` line, add:

```
    os_version = {{ $osVersion | quote }}
```

- [ ] **Step 3: Verify detection fragment**

Run:
```bash
cd ~/.local/share/chezmoi
chezmoi execute-template '{{ output "sh" "-c" "sw_vers -productVersion 2>/dev/null || echo" | trim }}'; echo
```
Expected: `26.5.2` (darwin host).

- [ ] **Step 4: Regenerate config and confirm live data**

Run:
```bash
cd ~/.local/share/chezmoi
chezmoi init
chezmoi data --format=json | grep '"os_version"'
```
Expected: `"os_version": "26.5.2"`.

- [ ] **Step 5: Commit**

```bash
cd ~/.local/share/chezmoi
git add home/.chezmoi.toml.tmpl
git commit -m "feat(chezmoi): detect os_version data"
```

---

### Task 5: End-to-end verification

**Files:**
- No code changes (verification only).

**Interfaces:**
- Consumes: all prior tasks.

- [ ] **Step 1: Live os-version gated resolution**

Run (uses live `.os_version`):
```bash
cd ~/.local/share/chezmoi
chezmoi execute-template '{{ includeTemplate "when/context" (merge (dict "item" (dict "when" (dict "enabled" (dict "os" (dict "type" "darwin" "version" ">=14.0"))))) .) }}'; echo
chezmoi execute-template '{{ includeTemplate "when/context" (merge (dict "item" (dict "when" (dict "enabled" (dict "os" (dict "type" "darwin" "version" ">=99.0"))))) .) }}'; echo
```
Expected: `true` then `false` (host is darwin 26.5.2).

- [ ] **Step 2: Existing skills script renders**

Run:
```bash
cd ~/.local/share/chezmoi
chezmoi execute-template < home/.chezmoiscripts/run_onchange_after_200_setup-skills.sh.tmpl 2>&1 | head -6
echo "exit: $?"
```
Expected: renders without template errors, exit 0.

- [ ] **Step 3: Dry-run apply clean**

Run:
```bash
cd ~/.local/share/chezmoi
chezmoi apply --dry-run 2>&1 | head -30; echo "exit: $?"
```
Expected: no template errors, exit 0.

- [ ] **Step 4: Commit verification checkpoint**

```bash
cd ~/.local/share/chezmoi
git commit --allow-empty -m "test: verify os version condition end-to-end"
```

---

## Self-Review

**Spec coverage:**
- Data detection per-OS incl. linux normalize + `""` fallback -> Task 4.
- Three `os` forms (scalar/list unchanged, map new) -> Task 2 (scalar/list preserved in else branches; map handled).
- `when/semver` lenient empty -> Task 1.
- Routing in check for enabled + disabled -> Task 2.
- context feeds `os_version` -> Task 3.
- verification -> Tasks 1-5.
All covered.

**Placeholder scan:** No TBD/TODO; every code step shows full content.

**Type consistency:** `when/semver` input `value:string, rule:string` matches calls in Task 2 (`.os_version|default ""`, `index $expected "version"`). `os_version` is a quoted string in toml (Task 4), read via `dig "os_version" ""` (Task 3) — string throughout. `type` matched via `when/match` supporting scalar or list, consistent with existing `os` semantics.
