# Pi and OMP shared bindings

Pi and OMP use the same Emacs editor chords. This page is the current
assignment. Tool defaults and status live in [pi.md](pi.md) and
[omp.md](omp.md).

Source configurations:

- `home/dot_pi/private_agent/modify_keybindings.json`
- `home/dot_omp/private_agent/modify_keybindings.yml`

WezTerm's default `Ctrl+R` reload is unbound so the key reaches the agent;
`Super+R` and `Ctrl+Shift+R` still reload WezTerm. Model cycle uses
`Ctrl+Shift+P` / `Ctrl+Shift+N` because macOS often drops `Ctrl+Alt+letter`.
WezTerm's command palette moves to `Super+Shift+P`; `Super+N` still opens a
window.

`Ctrl+P` in `/resume` still toggles path display. History bindings only
override model cycling while the main editor is focused.

## Emacs editor

| Keys | Current assignment |
| --- | --- |
| `Ctrl+P` / `Ctrl+N` | Previous / next line, or prompt history when the editor is empty |
| `Ctrl+B` / `Ctrl+F` | Cursor left / right |
| `Alt+B` / `Alt+F` | Word left / right |
| `Ctrl+A` / `Ctrl+E` | Line start / end |
| `Ctrl+H` / `Ctrl+D` | Delete character backward / forward |
| `Ctrl+K` / `Ctrl+U` | Delete to line end / start |
| `Ctrl+Y` / `Alt+Y` | Yank / yank-pop |
| `Ctrl+J` / `Shift+Enter` | New line |

## Prompt history and sessions

| Keys | Current assignment |
| --- | --- |
| `Ctrl+R` | Reverse-search prompt history |
| `Ctrl+Alt+R` | Rename session |

## Model cycle

| Keys | Current assignment |
| --- | --- |
| `Ctrl+Shift+P` | Next scoped model |
| `Ctrl+Shift+N` | Previous scoped model |
