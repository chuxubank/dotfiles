# Tool lifecycle

`home/.chezmoidata/tools.yaml` owns tool enablement, initialization, and cleanup.
Package declarations own installation; agent wiring belongs in
`home/.chezmoidata/integrations.yaml`.

## Initialization

A tool's `setup` list declares ordered initialization commands. Use it when the
CLI must own its configuration format or encrypted storage; prefer a managed
configuration file when chezmoi can safely own that file directly.

```yaml
tools:
  example:
    setup:
      - command:
          - example
          - config
          - set
          - credential
          - pass: {path: "<pass-entry>", field: "<field>"}
```

`command` is literal argv, never shell syntax. Its executable must be a string;
remaining arguments are strings or `pass: {path, field}` references. Do not put
secret values in literal arguments. The shared executor resolves references
through `~/bin/pass-field` at runtime and rejects missing or empty fields.
Rendered scripts contain declarations and encrypted-entry hashes, not plaintext
credentials. Command output and exception details are suppressed because CLIs
may echo secrets. Tool names identify failures; diagnose individual commands
manually when necessary. Credentials passed as argv can still be visible to
local process inspection while the CLI runs.

`run_onchange_after_101_setup-tools.py.tmpl` runs after package setup. Only
enabled tools participate; CI skips setup entirely. Each tool's inputs and
executables are checked before its first command. Commands then run in order,
stopping that tool on failure while still attempting other tools. Commands have
a bounded execution time and must be noninteractive and idempotent. Interactive
account authorization is a separate manual step.

All declared setup shares one chezmoi success/retry unit, with no custom receipt
or checkpoint. Declaration or encrypted pass-entry changes trigger setup. A
failure returns nonzero, so the next apply retries all enabled setup commands,
including commands that previously succeeded. This is not an ongoing drift
repair mechanism: manually deleted configuration does not itself trigger setup.
Keep independently retryable package installation and downloads outside this
initialization phase; do not add per-tool setup scripts for declaration-shaped
configuration. Disabling a tool stops setup but does not implicitly erase its
credentials; cleanup requires an explicit declaration below.

`scripts/test-tool-setup.py` exercises the shared executor with offline secret
readers and CLI stubs. Validation must not configure real accounts.

## Disabled-tool cleanup

`remove` lists chezmoi-managed files removed when a tool is disabled. `purge`
contains runtime cleanup entries, executed only when
`policies.purge_disabled_tools` is enabled.

### Path and command entries

Existing `purge` path strings keep their behavior: files go through
`.chezmoiremove`; trees ending in `/**` are moved to Trash by
`run_after_020_purge-disabled-tools.sh.tmpl`.

A command object first tries a tool's uninstaller for services, application
files, and data, then moves any declared path leftovers to Trash. It can coexist
with ordinary path strings for independently cleaned data:

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
- An available uninstaller runs first. A nonzero exit emits a warning with its
  status, but does not prevent declared path cleanup. Missing, dangling, or
  non-executable uninstallers simply skip this step; they are never reinstalled.
- Remaining declared paths are moved to Trash in all cases. Symlinks are moved
  themselves, never followed into shared skill sources. Success is determined
  by the final state: every declared path must be absent. Trash failure or
  leftovers fail apply and retry on the next run. If nothing remains, no Trash
  backend is needed. There is no permanent deletion fallback.
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
parallel `uninstall` field, missing-command option, or tool-specific script.
If a skill installer has left `~/.hermes/skills` behind, cleanup moves the
declared Hermes tree and launcher paths to Trash even when the launcher is gone
or the uninstaller leaves files behind. It does not change skill installation
or incremental updates for other agents. File cleanup alone cannot stop
services or undo system changes the uninstaller would own; inspect warnings
when the uninstaller fails. When available, the official uninstaller permanently
deletes owned files; review its live scope with `hermes uninstall --dry-run`
before enabling destructive cleanup.

`schemas/tools.schema.json` validates YAML declaration types, required fields,
allowed keys, argv/env values, conditions, and path syntax. `make verify` runs
schema validation before rendering templates. Cross-entry path overlap remains
in `verify/model`; exact ignore/removal behavior remains in `verify/contracts`.
`scripts/test-tool-purge.py` checks execution with offline uninstaller and Trash
stubs, including missing/dangling launchers, symlink safety, partial cleanup,
backend failure, and repeated apply. Validation never invokes real uninstallers
or trashes live files.
