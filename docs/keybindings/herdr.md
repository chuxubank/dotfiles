# Herdr keybindings

Source configuration:
`home/dot_config/herdr/config.toml`

Herdr owns agent-aware workspaces, mux tabs, and panes. Herdr's built-in
bindings are version-dependent, so “default” below means the previous
allocation in this repository.

## Workspace and pane bindings

| Keys | Default / previous allocation | Current assignment | Status |
| --- | --- | --- | --- |
| `Alt+1…9` | Select workspace 1–9 | Select workspace 1–9 | Unchanged |
| `Alt+0` | Toggle the sidebar | Toggle the sidebar | Unchanged |
| `Super+Arrow` | Focus the pane in that direction | Focus the pane in that direction | Unchanged |
| `Ctrl+1…9` | Select mux tab 1–9 | No Herdr binding; available to pane apps | **Changed** |

## Prefix

| Keys | Default / previous allocation | Current assignment | Status |
| --- | --- | --- | --- |
| `Ctrl+;` | `Ctrl+;` prefix | `Ctrl+;` prefix | Unchanged |
| `Ctrl+;` twice | Send a literal `Ctrl+;` | Send a literal `Ctrl+;` to the pane | Unchanged |

## Prefix bindings

Press `Ctrl+;`, then press the following key:

| Keys | Default / previous allocation | Current assignment | Status |
| --- | --- | --- | --- |
| `1…9` | No binding; direct `Ctrl+1…9` selected tabs | Select mux tab 1–9 | **Changed** |
| `n` | Select the next tab | Select the next tab | Unchanged |
| `p` | Select the previous tab | Select the previous tab | Unchanged |
| `h/j/k/l` | Focus a pane | Focus left/down/up/right pane | Unchanged |
| `b` | Toggle the sidebar | Toggle the sidebar | Unchanged |
| `Alt+h` | Pair Heeler | Pair Heeler | Unchanged |
| `Alt+l` | Apply the declared workspace layout | Apply the declared workspace layout | Unchanged |

The current Herdr tab shortcut is intentionally `Prefix+1…9`, not direct
`Ctrl+1…9`, so pane applications can use direct control-key chords where the
terminal permits them.
