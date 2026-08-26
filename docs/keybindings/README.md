# Terminal and mux keybindings

These files document both the tool defaults and the current assignments in
this repository. The status column distinguishes additions, deletions, and
changes:

- **Add** — a new binding was introduced.
- **Delete** — a previous/default binding was removed.
- **Change** — an existing binding now performs a different action.

## Layers

1. **Terminal layer** — Ghostty and WezTerm own terminal windows and tabs.
2. **Mux layer** — Herdr, Zellij, and Luvus own workspaces, mux tabs, and panes.
3. **Prefix layer** — mux structural commands use `Ctrl+;` as the prefix.

## Per-tool reference

- [Ghostty](ghostty.md)
- [WezTerm](wezterm.md)
- [Herdr](herdr.md)
- [Zellij](zellij.md)
- [Luvus](luvus.md)

## Shared allocation

| Keys | Tool default | Current assignment | Status |
| --- | --- | --- | --- |
| `Super+1…9` | Terminal tab selection | Ghostty/WezTerm terminal tab selection | Unchanged |
| `Ctrl+Tab` | Terminal tab next | Terminal tab next | Unchanged |
| `Ctrl+Shift+Tab` | Terminal tab previous | Terminal tab previous | Unchanged |
| `Alt+1…9` | Terminal/pane input | Herdr workspace selection | **Add** |
| `Ctrl+;` | Pane input / tool-specific | Herdr/Zellij/Luvus prefix | **Add** |
| `Ctrl+1…9` | Herdr/Zellij mux tab selection | No direct mux binding | **Delete** |
| `Ctrl+;` then `1…9` | No shared default | Herdr/Zellij/Luvus mux tab selection | **Add** |

See the tool-specific documents for the exact default and current binding
lists. “Default” means the upstream application default where it is available;
for Herdr it means the previous repository allocation because its built-in
bindings are version-dependent.
