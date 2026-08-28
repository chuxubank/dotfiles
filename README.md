# Misaka's dotfiles

[![CI](https://github.com/chuxubank/dotfiles/actions/workflows/ci.yaml/badge.svg)](https://github.com/chuxubank/dotfiles/actions/workflows/ci.yaml)

Managed with [chezmoi](https://github.com/twpayne/chezmoi).

```sh
chezmoi init chuxubank -a
```

## Terminal and mux key map

The terminal layer owns terminal tabs. Herdr, Zellij, and Luvus own their
internal workspaces, tabs, and panes.

The complete per-tool bindings are documented in
[`docs/keybindings/`](docs/keybindings/README.md):

| Tool | Detailed bindings |
| --- | --- |
| Ghostty | [`docs/keybindings/ghostty.md`](docs/keybindings/ghostty.md) |
| WezTerm | [`docs/keybindings/wezterm.md`](docs/keybindings/wezterm.md) |
| Herdr | [`docs/keybindings/herdr.md`](docs/keybindings/herdr.md) |
| Zellij | [`docs/keybindings/zellij.md`](docs/keybindings/zellij.md) |
| Luvus | [`docs/keybindings/luvus.md`](docs/keybindings/luvus.md) |
| Pi | [`docs/keybindings/pi.md`](docs/keybindings/pi.md) |

### Shared bindings

| Keys | Owner/action |
| --- | --- |
| `Super+1…9` | Ghostty/WezTerm terminal tab selection |
| `Ctrl+Tab` / `Ctrl+Shift+Tab` | Terminal tab next/previous |
| `Alt+1…9` | Herdr workspace selection |
| `Ctrl+;` | Herdr/Zellij/Luvus prefix |
| `Ctrl+;` then `1…9` | Herdr/Zellij/Luvus mux tab selection |
| `Super+Arrow` | Herdr/Zellij pane focus |

## Declared workspaces

Shared workspace, tab, pane, command, and agent declarations live in
[`home/.chezmoidata/workspaces.yaml`](home/.chezmoidata/workspaces.yaml).

- `herdr-layout [NAME...]` creates missing Herdr workspaces.
- `luvus-layout [NAME...]` creates missing Luvus workspaces through its CLI/API.
- Zellij layouts are generated under `~/.config/zellij/layouts/`.

Both runtime commands leave existing named workspaces untouched and focus the
workspace marked with `focus: true` after applying missing entries.
