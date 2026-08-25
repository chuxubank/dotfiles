# Misaka's dotfiles

[![CI](https://github.com/chuxubank/dotfiles/actions/workflows/ci.yaml/badge.svg)](https://github.com/chuxubank/dotfiles/actions/workflows/ci.yaml)

Managed with [chezmoi](https://github.com/twpayne/chezmoi).

```sh
chezmoi init chuxubank -a
```

## Terminal and mux key map

The terminal layer owns terminal tabs. Herdr and Zellij own their internal
workspaces, tabs, and panes.

### Ghostty and WezTerm

| Keys | Action |
| --- | --- |
| `Cmd+1…8` | Select terminal tab 1–8 |
| `Cmd+9` | Select the last terminal tab |
| `Cmd+T` | Create a terminal tab |
| `Cmd+W` | Close the current terminal surface/tab |
| `Ctrl+Tab` | Select the next terminal tab |
| `Ctrl+Shift+Tab` | Select the previous terminal tab |
| `Ctrl+Shift+Arrow` | Select the WezTerm pane in that direction |

### Shared mux bindings

| Keys | Herdr | Zellij |
| --- | --- | --- |
| `Prefix+1…9` | Select tab 1–9 | Select tab 1–9 |
| `Cmd+Arrow` | Focus the pane in that direction | Focus the pane in that direction |
| `Ctrl+;` | Enter prefix mode | Enter tmux/prefix mode |

### Herdr

| Keys | Action |
| --- | --- |
| `Alt+1…9` | Select workspace 1–9 |
| `Alt+0` | Toggle the sidebar |
| `Prefix+1…9` | Select tab 1–9 |
| `Prefix+n` / `Prefix+p` | Select the next/previous tab |
| `Prefix+h/j/k/l` | Focus a pane |
| `Prefix+b` | Toggle the sidebar |
| `Prefix+Alt+h` | Pair Heeler |
| `Prefix+Alt+l` | Apply the declared workspace layout |

Pressing `Ctrl+;` twice sends a literal `Ctrl+;` to the pane.

### Zellij prefix mode

Press `Ctrl+;`, then:

| Key | Action |
| --- | --- |
| `c` | Create a tab |
| `1…9` | Select tab 1–9 |
| `n` / `p` | Select the next/previous tab |
| `h/j/k/l` or arrows | Focus a pane |
| `"` | Split downward |
| `%` | Split to the right |
| `x` | Close the focused pane |
| `z` | Toggle focused-pane zoom |
| `[` | Enter scroll mode |
| `d` | Detach |
| `,` | Rename the tab |
| `Space` | Select the next swap layout |

Pressing `Ctrl+;` twice sends a literal `Ctrl+;` to the pane.

### Zellij mode shortcuts

| Keys | Mode/action |
| --- | --- |
| `Ctrl+P` | Pane mode |
| `Ctrl+T` | Tab mode |
| `Ctrl+N` | Resize mode |
| `Ctrl+H` | Move mode |
| `Ctrl+S` | Scroll mode |
| `Ctrl+O` | Session mode |
| `Ctrl+G` | Locked mode |
| `Ctrl+Q` | Quit Zellij |
