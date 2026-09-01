# Pi keybindings

Source configuration:
`home/dot_pi/private_agent/modify_keybindings.json`

Current Emacs chords are in the [shared bindings](agents.md). Pi is an
in-pane application. The upstream default list is in Pi's
[keybindings.md](https://github.com/earendil-works/pi-coding-agent/blob/main/docs/keybindings.md).
After editing, run `/reload` in Pi.

`Ctrl+P` / `Ctrl+N` use `tui.editor.historyPrevious` / `historyNext`.

Model cycle moved to `Alt+N` / `Alt+P`, the Emacs next/previous pair. `pi-tui`
matches `shift+ctrl+<key>` only through kitty or modifyOtherKeys sequences and
has no legacy fallback for it, while `alt+<key>` does fall back to `ESC` + the
key. A Luvus pane offers neither enhanced encoding, so the shifted chord is
unreachable there. Pi upstream already substitutes `Alt+P` on Windows for the
same reason. Letters rather than punctuation because OMP shares these chords and
matches only `alt+<letter>`. See [agents.md](agents.md).

## Deltas from upstream

| Keys | Pi default | Current assignment | Status |
| --- | --- | --- | --- |
| `Ctrl+P` | Cycle to the next scoped model | Previous prompt history | **Change** |
| `Ctrl+N` | No editor history binding | Next prompt history | **Add** |
| `Ctrl+H` | No delete-backward binding | Delete character backward | **Add** |
| `Ctrl+R` | Rename session | Reverse-search prompt history | **Change** |
| `Ctrl+Shift+P` | Cycle backward | Not bound; unreachable inside a Luvus pane | **Delete** |
| `Alt+N` | No assignment | Next scoped model | **Add** |
| `Alt+P` | No assignment on macOS (Windows: cycle backward) | Previous scoped model | **Add** |
| `Ctrl+Alt+R` | No assignment (`Ctrl+R` renamed sessions) | Rename session | **Change** |
