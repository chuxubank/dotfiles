# Pi keybindings

Source configuration:
`home/dot_pi/private_agent/modify_keybindings.json`

Pi is an in-pane application. In the current terminal setup, `Ctrl+P`,
`Ctrl+N`, `Ctrl+R`, and the model-cycle chords reach Pi without terminal
overrides.

The upstream default list is in Pi's
[keybindings.md](https://github.com/earendil-works/pi-coding-agent/blob/main/docs/keybindings.md).
After editing, run `/reload` in Pi.

## Emacs editor

| Keys | Pi default | Current assignment | Status |
| --- | --- | --- | --- |
| `Ctrl+P` | Cycle to the next scoped model | Previous prompt history | **Change** |
| `Ctrl+N` | No editor history binding | Next prompt history | **Add** |
| `Ctrl+B` / `Ctrl+F` | Cursor left / right | Cursor left / right | Unchanged |
| `Alt+B` / `Alt+F` | Word left / right | Word left / right | Unchanged |
| `Ctrl+A` / `Ctrl+E` | Line start / end | Line start / end | Unchanged |
| `Ctrl+H` | No delete-backward binding | Delete character backward | **Add** |
| `Ctrl+D` | Delete character forward | Delete character forward | Unchanged |
| `Ctrl+K` / `Ctrl+U` | Delete to line end / start | Delete to line end / start | Unchanged |
| `Ctrl+Y` / `Alt+Y` | Yank / yank-pop | Yank / yank-pop | Unchanged |
| `Ctrl+J` / `Shift+Enter` | New line | New line | Unchanged |

`Ctrl+P` in `/resume` still toggles path display. History bindings only
override model cycling while the main editor is focused.

## Prompt history and sessions

`pi-input-history` keeps reverse search on `Ctrl+R` (readline/Emacs).
Session rename moves to the Meta variant so Pi stops warning about the
built-in `app.session.rename` chord. WezTerm's default `Ctrl+R` reload is
unbound so the key reaches Pi; `Super+R` and `Ctrl+Shift+R` still reload
WezTerm.

| Keys | Pi default | Current assignment | Status |
| --- | --- | --- | --- |
| `Ctrl+R` | Rename session | Reverse-search prompt history | **Change** |
| `Ctrl+Alt+R` | No assignment (`Ctrl+R` renamed sessions) | Rename session | **Change** |

## Model cycle

WezTerm keeps `Ctrl+Shift+P` for the command palette, so Pi does not use
that chord. Cycle uses the Meta variants of the Emacs history keys.

| Keys | Pi default | Current assignment | Status |
| --- | --- | --- | --- |
| `Ctrl+Alt+P` | No assignment (`Ctrl+P` cycled models) | Next scoped model | **Change** |
| `Ctrl+Alt+N` | No assignment (`Ctrl+Shift+P` cycled backward) | Previous scoped model | **Change** |
