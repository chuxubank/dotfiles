# Misaka's dotfiles

[![CI](https://github.com/chuxubank/dotfiles/actions/workflows/ci.yaml/badge.svg)](https://github.com/chuxubank/dotfiles/actions/workflows/ci.yaml)

Managed with [chezmoi](https://github.com/twpayne/chezmoi).

```sh
chezmoi init chuxubank -a
```

## Terminal and mux key map

The terminal layer owns terminal tabs. Herdr and Zellij own their internal
workspaces, tabs, and panes.

The complete per-tool bindings are documented in
[`docs/keybindings/`](docs/keybindings/README.md):

| Tool | Detailed bindings |
| --- | --- |
| Ghostty | [`docs/keybindings/ghostty.md`](docs/keybindings/ghostty.md) |
| WezTerm | [`docs/keybindings/wezterm.md`](docs/keybindings/wezterm.md) |
| Herdr | [`docs/keybindings/herdr.md`](docs/keybindings/herdr.md) |
| Zellij | [`docs/keybindings/zellij.md`](docs/keybindings/zellij.md) |

### Shared bindings

| Keys | Owner/action |
| --- | --- |
| `Super+1…9` | Ghostty/WezTerm terminal tab selection |
| `Ctrl+Tab` / `Ctrl+Shift+Tab` | Terminal tab next/previous |
| `Alt+1…9` | Herdr workspace selection |
| `Ctrl+;` | Herdr/Zellij prefix |
| `Ctrl+;` then `1…9` | Herdr/Zellij mux tab selection |
| `Super+Arrow` | Herdr/Zellij pane focus |
