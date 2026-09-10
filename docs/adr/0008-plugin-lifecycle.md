# Centralize plugin lifecycle runners

Plugin declarations are tool-scoped data under `home/.chezmoidata/plugins/`. They must not create one chezmoi script per consuming agent: that makes script count and lifecycle ordering grow with every plugin manager.

`plugin-managers.yaml` declares the finite differences between supported managers: phase, inventory shape, identity, commands, PATH additions, and marketplace handling. `plugins/engine.py` implements reconciliation. Two fixed scripts are the only lifecycle entry points: `reconcile-plugins` runs before apply for Pi, whose undeclared packages must be read from the old settings before chezmoi rewrites them; `setup-plugins` runs after apply for managers whose configuration must already be applied. Their basenames deliberately differ because chezmoi strips script attributes when deriving target names.

Adding a manager means adding data and, only when the finite schema is insufficient, extending the shared engine. It must not add `setup-<agent>-plugins` scripts. Managers whose plugin state is rendered directly into owned config, such as Claude Code and Codex, remain config-only consumers and need no lifecycle manager.
