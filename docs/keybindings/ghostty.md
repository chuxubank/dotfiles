# Ghostty keybindings

Source configuration:
`home/dot_config/ghostty/config`

Ghostty owns the terminal window/tab layer. Ghostty's macOS defaults can be
listed locally with:

```sh
ghostty +list-keybinds --default
```

## Terminal tabs

| Keys | Default | Current assignment | Status |
| --- | --- | --- | --- |
| `Super+1…8` | Select terminal tab 1–8 | Select terminal tab 1–8 | Unchanged |
| `Super+9` | Select the last terminal tab | Select the last terminal tab | Unchanged |
| `Super+T` | Create a terminal tab | Create a terminal tab | Unchanged |
| `Super+W` | Close the current surface/tab | Close the current surface/tab | Unchanged |
| `Ctrl+Tab` | Select the next terminal tab | Select the next terminal tab | Unchanged |
| `Ctrl+Shift+Tab` | Select the previous terminal tab | Select the previous terminal tab | Unchanged |

## Deliberate unbindings

These bindings are removed from Ghostty so that the mux or pane layer can own
them. The **Changed** rows are the important differences from the terminal
defaults/previous allocation.

| Keys | Default / previous allocation | Current assignment | Status |
| --- | --- | --- | --- |
| `Ctrl+Shift+T` | Terminal/mux tab command | Unbound; passed to the pane | **Changed** |
| `Ctrl+Shift+W` | Terminal/mux close command | Unbound; passed to the pane | **Changed** |
| `Alt+1…9` | Terminal shortcut, if provided by the platform build | Unbound; Herdr selects workspaces | **Changed** |
| `Super+Alt+Arrow` | Terminal/mux pane command | Unbound; mux owns pane navigation | **Changed** |
| `Super+Ctrl+Arrow` | Terminal/mux pane command | Unbound; reserved for pane applications | **Changed** |
| `Super+[` / `Super+]` | Terminal tab navigation | Unbound; kept free for the mux layer | **Changed** |
| `Super+Shift+[` / `Super+Shift+]` | Terminal tab navigation | Unbound; kept free for the mux layer | **Changed** |

`macos-option-as-alt = true` enables the macOS Alt mapping.

## Mux usage inside Ghostty

For Herdr or Zellij:

```text
Ctrl+; → 1…9
```

The prefix and digit are separate key presses. Direct `Ctrl+1…9` is not the
configured mux-tab shortcut.
