# Pi keybindings

Source configuration:
`home/dot_pi/private_agent/modify_keybindings.json`

Current Emacs chords are in the [shared bindings](README.md). Pi is an
in-pane application. The upstream default list is in Pi's
[keybindings.md](https://github.com/earendil-works/pi-coding-agent/blob/main/docs/keybindings.md).
After editing, run `/reload` in Pi.

`Ctrl+P` / `Ctrl+N` use `tui.editor.historyPrevious` / `historyNext`.

Model cycle moved to `Alt+N` / `Alt+P`, the Emacs next/previous pair. `pi-tui`
matches `shift+ctrl+<key>` only through kitty or modifyOtherKeys sequences and
has no legacy fallback for it, while `alt+<key>` does fall back to `ESC` + the
key. A Luvus pane offers neither enhanced encoding, so the shifted chord is
unreachable there. See the [shared bindings](README.md).

The action IDs are `alt+down` / `alt+up`, not `alt+n` / `alt+p` as in OMP.
`pi-tui`'s `LEGACY_SEQUENCE_KEY_IDS` aliases `ESC n` to the key id `alt+down`
and `ESC p` to `alt+up`, because Emacs `M-n` / `M-p` and the down/up arrows are
the same motion. Binding `alt+n` here registers but never fires — the event Pi
sees is `alt+down`. Pressing `M-n` / `M-p` reaches these, and `Alt+Down` /
`Alt+Up` work as well.

That takes `Alt+Up` from `app.message.dequeue`, which moves to `Alt+Q` — Pi's
own Windows fallback for that action, unused on macOS.

## Deltas from upstream

| Keys | Pi default | Current assignment | Status |
| --- | --- | --- | --- |
| `Ctrl+P` | Cycle to the next scoped model | Previous prompt history | **Change** |
| `Ctrl+N` | No editor history binding | Next prompt history | **Add** |
| `Ctrl+H` | No delete-backward binding | Delete character backward | **Add** |
| `Ctrl+R` | Rename session | Reverse-search prompt history | **Change** |
| `Ctrl+Shift+P` | Cycle backward | Not bound; unreachable inside a Luvus pane | **Delete** |
| `Alt+N` / `Alt+Down` | Reorder a model down (selector only) | Next scoped model | **Add** |
| `Alt+P` / `Alt+Up` | Dequeue a queued message | Previous scoped model | **Change** |
| `Alt+Q` | No assignment on macOS (Windows: dequeue) | Dequeue a queued message | **Add** |
| `Ctrl+Alt+R` | No assignment (`Ctrl+R` renamed sessions) | Rename session | **Change** |
