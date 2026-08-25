# Zellij keybindings

Source configuration:
`home/dot_config/zellij/config.kdl.tmpl`

Zellij uses `clear-defaults=true`. The default column below refers to the
upstream default preset; the current column is the explicit repository map.

## Mode entry and shared shortcuts

| Keys | Zellij default | Current assignment | Status |
| --- | --- | --- | --- |
| `Ctrl+;` | Primary modifier / mode entry | Enter tmux/prefix mode | **Change** |
| `Ctrl+P` | Enter pane mode | Enter pane mode | Unchanged |
| `Ctrl+T` | Enter tab mode | Enter tab mode | Unchanged |
| `Ctrl+N` | Enter resize mode | Enter resize mode | Unchanged |
| `Ctrl+H` | Enter move mode | Enter move mode | Unchanged |
| `Ctrl+S` | Enter scroll mode | Enter scroll mode | Unchanged |
| `Ctrl+O` | Enter session mode | Enter session mode | Unchanged |
| `Ctrl+G` | Enter locked mode | Enter locked mode | Unchanged |
| `Ctrl+Q` | Quit Zellij | Quit Zellij | Unchanged |

Pressing `Ctrl+;` twice sends a literal `Ctrl+;` to the pane.

## Prefix / tmux mode

Press `Ctrl+;`, then press the following key:

| Key | Zellij default / previous allocation | Current assignment | Status |
| --- | --- | --- | --- |
| `c` | Create a tab | Create a tab | Unchanged |
| `1…9` | No binding in prefix mode | Select tab 1–9 | **Add** |
| `n` / `p` | Select the next/previous tab | Select the next/previous tab | Unchanged |
| `h/j/k/l` or arrows | Focus a pane | Focus a pane | Unchanged |
| `"` | Split downward | Split downward | Unchanged |
| `%` | Split to the right | Split to the right | Unchanged |
| `x` | Close the focused pane | Close the focused pane | Unchanged |
| `z` | Toggle focused-pane zoom | Toggle focused-pane zoom | Unchanged |
| `[` | Enter scroll mode | Enter scroll mode | Unchanged |
| `d` | Detach | Detach | Unchanged |
| `,` | Rename the tab | Rename the tab | Unchanged |
| `Space` | Select the next swap layout | Select the next swap layout | Unchanged |

## Direct pane binding

| Keys | Zellij default | Current assignment | Status |
| --- | --- | --- | --- |
| `Super+Left/Down/Up/Right` | No assignment | Focus the pane in that direction | **Add** |

The current Zellij mux-tab shortcut is `Prefix+1…9`, not direct
`Ctrl+1…9`.

The previous direct `Ctrl+1…9` tab bindings were removed:

| Keys | Previous allocation | Current assignment | Status |
| --- | --- | --- | --- |
| `Ctrl+1…9` | Select mux tab 1–9 | No Zellij binding | **Delete** |
