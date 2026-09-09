# Declare agent integrations behind one lifecycle engine

Tools such as RTK, Worktrunk, Herdr, Termio, and Orca install files into other
agents' configuration trees. Listing those files in the owner's `remove` or
`purge` paths would make `disabled-ignore` ignore the target agent's directory,
so the owner must instead remove only its own injected entries.

Per-owner scripts and Python adapters caused implementation count and execution
order to grow with every owner. They also repeated enablement, platform, command,
and cleanup logic.

The repository has two fixed lifecycle entry points:

- `run_before_000_00_teardown-integrations.py.tmpl` runs on every apply and
  reconciles disabled owners. Teardown is idempotent because an external app may
  inject a hook again after a previous apply.
- `run_onchange_after_110_setup-integrations.py.tmpl` reconciles enabled owners
  when its rendered declarations or the shared engine change.

A tool participates only through `tools.yaml`: `integrations` declares target
agents and arguments; `integration_lifecycle` declares platform support,
commands, target environment, cleanup, and optional post-install file moves.
`integration_lifecycle.setup: false` declares a cleanup-only owner. Shared target
roots live in `.chezmoidata/integrations.yaml`.

No integration owner gets a file under `.chezmoiscripts` or a private
`<owner>/run.py` / `<owner>/cleanup.py`. `integrations/owners` selects owners,
`integrations/payload` resolves target enablement, and `integrations/engine.py`
executes a finite action schema. Data cannot contain arbitrary Python.

Supported cleanup actions are standalone file removal, structural JSON hook
filtering, marked Markdown-line removal, marker-guarded file removal, and managed
block removal. Post-install may move one generated file while applying literal
text replacements. New behavior should first be expressed by composing these
actions; extending the shared engine requires a genuinely new reusable action.

Cleanup must preserve entries installed by other owners. CLI uninstall is best
effort; local conservative cleanup is the final invariant.
