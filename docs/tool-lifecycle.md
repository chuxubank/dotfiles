# Disabled-tool cleanup

`home/.chezmoidata/tools.yaml` owns tool enablement and cleanup declarations.
`remove` lists chezmoi-managed files removed when a tool is disabled. `purge`
contains runtime cleanup entries, executed only when
`policies.purge_disabled_tools` is enabled.

## Path and command entries

Existing `purge` path strings keep their behavior: files go through
`.chezmoiremove`; trees ending in `/**` are moved to Trash by
`run_after_020_purge-disabled-tools.sh.tmpl`.

A command object lets a tool's uninstaller own services, application files, and
data. It can coexist with ordinary path strings for independently cleaned data:

```yaml
tools:
  example:
    when: { enabled: false }
    remove:
      - ".example/config.yaml"
    purge:
      - command: ["{home}/.local/bin/example", uninstall, --full, --yes]
        when:
          enabled:
            os: [darwin, linux]
        env:
          EXAMPLE_HOME: "{home}/.example"
        paths:
          - ".example/**"
          - ".local/bin/example"
      - ".cache/example-downloads/**"
```

- `command` is a nonempty argv array, not a shell command. Arguments and
  environment values are literal; only a leading `{home}` expands to `HOME`.
  `env` supplies optional per-command overrides within a subshell, not inline
  shell assignments. Do not put credentials in these declarations.
- `when` uses the shared host-condition schema. The command runs only when its
  tool is disabled, its own condition matches, and the purge policy is on.
- `paths` is a nonempty list of narrow home-relative cleanup targets. A trailing
  `/**` denotes a tree; its root must be absent after the command. Other globs
  and parent traversal are forbidden. Dangling symlinks count as leftovers.
- The same `paths` derive source-state ignore: `foo/**` ignores `foo`; an exact
  file ignores only that file, never its parent. This allows launchers in shared
  `.local/bin` without hiding unrelated commands. Ignore is independent of the
  command's platform condition and the purge policy.
- Missing executables are a no-op only if all declared targets are absent.
  A nonzero command exit stops apply. A zero exit with remaining targets also
  fails. There is no automatic reinstall or destructive cleanup fallback.
- `run_before_010_purge-disabled-tool-commands.sh.tmpl` executes command entries
  before chezmoi removes managed configuration. It runs on every apply, so a
  failed removal can retry on the next apply. Commands should be idempotent.
- Command-owned paths are never sent to `.chezmoiremove` or the generic
  directory purge, even on platforms excluded by the command's `when`.
  Independent string entries still run normally. Do not duplicate or overlap
  command-owned targets with string purges or another command's targets.
- `remove` retains its normal managed-file semantics. Use a command object's
  `paths` for shared-tree files; string `remove`/`purge` entries still derive
  their parent ignore and must be under tool-owned directories.

Hermes declares `hermes uninstall --full --yes` inside `purge`; there is no
parallel `uninstall` field or tool-specific script. Unlike Trash-based purges,
its official uninstaller permanently deletes owned files. Review its live scope
with `hermes uninstall --dry-run` before enabling destructive cleanup.

`schemas/tools.schema.json` validates YAML declaration types, required fields,
allowed keys, argv/env values, conditions, and path syntax. `make verify` runs
schema validation before rendering templates. Cross-entry path overlap remains
in `verify/model`; exact ignore/removal behavior remains in `verify/contracts`.
`scripts/test-tool-purge.py` checks execution with offline stubs only. Validation
never invokes real uninstallers.
