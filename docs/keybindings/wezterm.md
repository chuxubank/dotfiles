# WezTerm keybindings

Source configurations:

- `home/dot_config/wezterm/keys.lua`
- `home/dot_config/wezterm/wezterm.lua`

The upstream default list can be inspected with:

```sh
wezterm show-keys --lua
```

WezTerm owns terminal tabs and its own GUI/mux controls. Herdr and Zellij
receive mux commands after the `Ctrl+;` prefix.

## Terminal and pane defaults

| Keys | WezTerm default | Current assignment | Status |
| --- | --- | --- | --- |
| `Super+T` | Create a terminal tab | Create a terminal tab | Unchanged |
| `Super+W` | Close the current terminal tab | Close the current terminal tab | Unchanged |
| `Super+1…8` | Select terminal tab 1–8 | Select terminal tab 1–8 | Unchanged |
| `Super+9` | Select the last terminal tab | Select the last terminal tab | Unchanged |
| `Ctrl+Tab` | Select the next terminal tab | Select the next terminal tab | Unchanged |
| `Ctrl+Shift+Tab` | Select the previous terminal tab | Select the previous terminal tab | Unchanged |
| `Ctrl+Shift+Arrow` | Focus the WezTerm pane | Focus the WezTerm pane | Unchanged |
| `Ctrl+Shift+Alt+Arrow` | Resize the WezTerm pane | Resize the WezTerm pane | Unchanged |
| `Ctrl+Shift+Alt+"` / `%` | Split pane vertically/horizontally | Same split actions | Unchanged |
| `Ctrl+1…9` | No direct WezTerm tab assignment in this version | Sent through; Herdr has no direct binding | Unchanged |
| `Ctrl+Shift+1…9` | Select terminal tab 1–9 | Select terminal tab 1–9 | Unchanged |

## Deliberate overrides and additions

| Keys | WezTerm default / previous allocation | Current assignment | Status |
| --- | --- | --- | --- |
| `Ctrl+Shift+T` | Create a terminal tab | Unbound; passed to the pane | **Changed** |
| `Super+Shift+T` | Create a default-domain tab | Unbound; passed to the pane | **Changed** |
| `Ctrl+Shift+W` | Close the current terminal tab | Unbound; passed to the pane | **Changed** |
| `Super+[` / `Super+]` | Select the previous/next tab | Unbound; kept free for the mux | **Changed** |
| `Super+Shift+[` / `Super+Shift+]` | Select the previous/next tab | Unbound; kept free for the mux | **Changed** |
| `Ctrl+Shift+Z` | Toggle pane zoom | Unbound; passed to the pane | **Changed** |
| `Ctrl+Shift+B` | No assignment | Toggle window opacity | **Added** |
| `Ctrl+Shift+Alt+L` | No assignment | Open the WezTerm launcher | **Added** |
| `Super+Arrow` | No assignment | Passed to Herdr/Zellij for pane focus | **Added** |

## Mux usage inside WezTerm

For Herdr or Zellij:

```text
Ctrl+; → 1…9
```

WezTerm's direct `Ctrl+1…9` is not the mux-tab shortcut. If direct
`Ctrl+1…9` mux switching is restored later, the terminal/pane ownership must
be changed in both WezTerm and the mux configuration.
