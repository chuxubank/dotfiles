# Cursor plugins

`home/.chezmoidata/plugins/cursor.yaml` declares Cursor-only plugins. Each
`source` is a repository archive URL; `name` is the plugin directory within
that archive (beneath the archive’s repository root).

`home/dot_cursor/plugins/local/.chezmoiexternal.toml.tmpl` uses the shared
plugin resolver and tool gating to extract enabled plugins into
`~/.cursor/plugins/local/<name>/`. Only the selected plugin subtree is
materialized, with a 24-hour refresh period. `exact` applies within each
managed plugin, not to the whole local-plugin directory. No account-level
marketplace state, runtime caches, or LLM installation prompts are managed.

After applying, restart Cursor or run **Developer: Reload Window**, then check
**Customize** for the plugin’s skills and agents. See Cursor’s
[local-plugin documentation](https://cursor.com/docs/plugins#test-plugins-locally).
Teams/Enterprise must allow local plugin imports. An installed marketplace
plugin with the same name takes precedence over the local copy; remove that
marketplace installation in Customize if you want the chezmoi-managed copy
to take effect.

For pstack, `/poteto-mode` is the workflow entry point and `/poteto-help`
provides guidance. Optional `/setup-pstack` chooses models and reasoning
budgets and writes `~/.cursor/rules/pstack-models.mdc`; that personal choice
is not made by this installation.
