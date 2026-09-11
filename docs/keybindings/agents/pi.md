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

Enter and Alt+Enter are swapped for the message queue. Pi's default Enter
steers (after the current tool batch); Alt+Enter follows up (after the run is
idle). Here Enter follows up, Alt+Enter steers. Idle Enter still submits,
because follow-up with no active run falls through to submit.

## Ghost suggestions shadow four chords

`pi-autosuggestions` (declared in `home/.chezmoidata/plugins/pi.yaml`) draws a
zsh-autosuggestions-style ghost after the cursor. Its editor intercepts four
chords **before** delegating to the app keybindings, so while a ghost is
visible those chords do not reach the actions below:

| Keys | Assignment here | While a ghost shows |
| --- | --- | --- |
| `Alt+Up` / `M-p` | Previous scoped model | Previous ghost candidate |
| `Alt+Down` / `M-n` | Next scoped model | Next ghost candidate |
| `Alt+F` | Word right | Accept one ghost word |
| `Right` | Cursor right | Accept the whole ghost |

The guard is `activeGhost() && cursorAtLineEnd()`, so the chords return to their
normal actions with no ghost on screen or with the cursor away from the line end
— `Ctrl+B` is enough to release them. The values above are read from the
package's `handleInput`, not measured; the extension exposes no setting to
disable the interception, so treat them as fixed until the package changes.

The ghost is not limited to `!` bash mode. The history strategy runs on every
line, so typing the prefix of an earlier prompt raises a ghost in ordinary prose
too, and the model cycle is shadowed there as well. That is the case worth
knowing about: bash-mode-only shadowing would be harmless, since word-right and
model-switching are rare mid-command.

`Alt+Q` (dequeue) and `Ctrl+R` (reverse search) are untouched. `Ctrl+R` lives on
`registerShortcut` plus an overlay component rather than the editor, so it
survives regardless.

## Deltas from upstream

| Keys | Pi default | Current assignment | Status |
| --- | --- | --- | --- |
| `Ctrl+P` | Cycle to the next scoped model | Previous prompt history | **Change** |
| `Ctrl+N` | No editor history binding | Next prompt history | **Add** |
| `Ctrl+H` | No delete-backward binding | Delete character backward | **Add** |
| `Ctrl+R` | Rename session | Reverse-search prompt history | **Change** |
| `Ctrl+Shift+P` | Cycle backward | Not bound; unreachable inside a Luvus pane | **Delete** |
| `Alt+N` / `Alt+Down` | Reorder a model down (selector only) | Next scoped model; ghost candidate while one shows | **Add** |
| `Alt+P` / `Alt+Up` | Dequeue a queued message | Previous scoped model; ghost candidate while one shows | **Change** |
| `Alt+Q` | No assignment on macOS (Windows: dequeue) | Dequeue a queued message | **Add** |
| `Enter` | Submit; steer while working | Submit; follow-up while working | **Change** |
| `Alt+Enter` | Follow-up while working | Steer while working | **Change** |
| `Ctrl+Alt+R` | No assignment (`Ctrl+R` renamed sessions) | Rename session | **Change** |
| `Right` | Cursor right | Accept ghost suggestion while one shows | **Add** |
| `Alt+F` | Word right | Accept one ghost word while one shows | **Change** |
| `Ctrl+Right` | No assignment | Accept one ghost word while one shows | **Add** |
| `Escape` | Abort; restore queued messages | Also dismisses the ghost | **Add** |
