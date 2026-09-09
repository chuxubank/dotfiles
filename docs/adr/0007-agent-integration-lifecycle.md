# Dispatch agent integrations through fixed lifecycle scripts

Tools such as RTK, Worktrunk, Herdr, Termio, and Orca install files into other
agents' configuration trees. Listing those files in the owner's `remove` or
`purge` paths would make `disabled-ignore` ignore the target agent's directory,
so the owner must instead remove only its own injected entries.

Per-owner chezmoi scripts caused the installed script count and execution order
to grow with every integration owner. They also repeated enablement, platform,
and Python checks.

The repository now has two fixed lifecycle entry points:

- `run_before_000_00_teardown-integrations.py.tmpl` runs on every apply and
  reconciles disabled owners. Teardown must be idempotent because an external
  application may inject a hook again after a previous apply.
- `run_onchange_after_110_setup-integrations.py.tmpl` reconciles enabled owners
  when its rendered owner list or adapter implementation changes.

A tool participates by declaring `integrations` in `tools.yaml` and providing
`.chezmoitemplates/<owner>/run.py`. The adapter accepts `mode=setup|teardown`.
`integration_lifecycle.setup: false` declares a cleanup-only adapter;
`integration_lifecycle.os` limits both modes to listed operating systems.
Adding an owner must not add another file under `.chezmoiscripts`.

`integrations/owners` resolves owners for each mode, `integrations/dispatch.py`
runs their adapters, `integrations/payload` resolves target-agent enablement,
and `integrations/loop.py` provides the common install/uninstall loop. Vendor
commands and exceptional transformations remain in owner adapters because they
are real behavioral differences.

An owner adapter must be idempotent and conservative. Standalone owner files may
be removed, but shared JSON/TOML/Markdown must be edited structurally or through
an owner marker. Cleanup must preserve entries installed by other owners. CLI
uninstall is best effort; local cleanup is the final invariant.
