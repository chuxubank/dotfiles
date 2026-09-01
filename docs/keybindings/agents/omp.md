# OMP keybindings

Source configuration:
`home/dot_omp/private_agent/modify_keybindings.yml`

Current Emacs chords are in the [shared bindings](README.md). OMP is an
in-pane application. User remaps live in `~/.omp/agent/keybindings.yml`.
The upstream default list is in OMP's
[keybindings.md](https://github.com/can1357/oh-my-pi/blob/main/docs/keybindings.md).
After editing, restart OMP or run `/hotkeys` to inspect the active chords.

OMP has no `tui.editor.historyPrevious` / `historyNext` actions. `Ctrl+P` /
`Ctrl+N` are added to `cursorUp` / `cursorDown`. Empty-composer `Ctrl+D`
exits (readline EOF) via `extensions/emacs-eof.ts`; with text it still
deletes forward. Double `Ctrl+C` still exits (clear first, exit second).
Session-picker `app.session.delete` is unchanged.

Model cycle moved to `Alt+N` / `Alt+P`, the Emacs next/previous pair. OMP's
chord encoder folds ctrl chords through `toUpperCase().charCodeAt(0) & 31`, so
`Ctrl+Shift+P` and `Ctrl+P` both encode to `0x10`; with no kitty protocol in a
Luvus pane to disambiguate them, the shifted chord is unreachable. The
replacements must be letters: OMP lists a rebound `alt+<symbol>` in `/hotkeys`
but never matches it. Verified by binding `app.model.select` to `alt+u` (fires)
versus `alt+.` (does not); `alt+shift+<letter>` fires too. `Alt+P` is OMP's own
`selectTemporary`, moved to `Alt+Shift+M` beside `model.select` on `Alt+M`.
See the [shared bindings](README.md).

## Deltas from upstream

| Keys | OMP default | Current assignment | Status |
| --- | --- | --- | --- |
| `Ctrl+P` | Cycle to the next scoped model | Previous line / prompt history | **Change** |
| `Ctrl+N` | No editor binding | Next line / prompt history | **Add** |
| `Ctrl+H` | No delete-backward binding | Delete character backward | **Add** |
| `Ctrl+D` | Exit (saves the current prompt as a draft) | Delete forward; exit when the composer is empty | **Change** |
| `Ctrl+R` | Search prompt history (editor); rename session (picker) | Reverse-search prompt history; rename on `Ctrl+Alt+R` | **Change** |
| `Ctrl+Alt+R` | No assignment (`Ctrl+R` renamed sessions) | Rename session | **Change** |
| `Ctrl+Shift+P` | Cycle backward | Not bound; unreachable inside a Luvus pane | **Delete** |
| `Alt+N` | No assignment | Next scoped model | **Add** |
| `Alt+P` | Select a temporary model | Previous scoped model | **Change** |
| `Alt+Shift+M` | No assignment | Select a temporary model (was `Alt+P`) | **Add** |
