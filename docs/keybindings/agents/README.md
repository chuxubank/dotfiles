# In-pane agent keybindings

Agents run inside a mux pane and share one Emacs editor chord set. This page is
the current assignment for that shared set. Per-agent defaults, and the few
implementation differences that force a chord apart, live in the tool files:

- [Pi](pi.md)
- [OMP](omp.md)

Source configurations:

- `home/dot_pi/private_agent/modify_keybindings.json`
- `home/dot_omp/private_agent/modify_keybindings.yml`

WezTerm's default `Ctrl+R` reload is unbound so the key reaches the agent;
`Super+R` and `Ctrl+Shift+R` still reload WezTerm.

Model cycle uses `Alt+N` / `Alt+P` — the Emacs next/previous pair — rather than
`Ctrl+Shift+P` / `Ctrl+Shift+N`. This keeps the modifier hierarchy consistent:
Ctrl moves by character and line (`Ctrl+N` / `Ctrl+P`), Meta moves by the larger
unit, exactly as `Ctrl+F` is a character and `Alt+F` a word.

The move off `Ctrl+Shift` is forced by the input path, not preference. Luvus
panes advertise neither the kitty keyboard protocol nor xterm modifyOtherKeys,
and under legacy encoding `Ctrl+letter` is a caseless control byte, so
`Ctrl+Shift+P` arrives as plain `Ctrl+P` (`0x10`) and the model cycle can never
fire. Alt chords have a legacy form, `ESC` + the key, so they arrive intact.
Upstream Pi already falls back to `Alt+P` on Windows for the same reason.

The chords are letters because OMP matches only `alt+<letter>` and
`alt+shift+<letter>`. A rebound `alt+<symbol>` such as `alt+.` is accepted by
the config parser and listed by `/hotkeys`, but never fires. Pi matches both, so
letters are the shared subset.

`Alt+P` is OMP's own `app.model.selectTemporary` by default. It moves to
`Alt+Shift+M`, beside `app.model.select` on `Alt+M`.

Because `Ctrl+Shift+P` cannot reach the agent, WezTerm keeps its own command
palette on it; `Super+Shift+P` is a second palette chord.

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
| `Alt+N` | Next scoped model |
| `Alt+P` | Previous scoped model |
| `Alt+M` / `Alt+Shift+M` | Open the model selector / pick a temporary model (OMP) |
