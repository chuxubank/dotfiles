# Pi keybindings

Source configuration:
`home/dot_pi/private_agent/modify_keybindings.json`

Current Emacs chords are in the [shared bindings](README.md). Pi is an
in-pane application. The upstream default list is in Pi's
[keybindings.md](https://github.com/earendil-works/pi-coding-agent/blob/main/docs/keybindings.md).
After editing, run `/reload` in Pi.

`Ctrl+P` / `Ctrl+N` use `tui.editor.historyPrevious` / `historyNext`.

Model cycle moved to `Alt+N` / `Alt+P`, the Emacs next/previous pair, keeping
the modifier hierarchy in the [shared bindings](README.md): Ctrl moves by
character and line, Meta by the larger unit. `Ctrl+Shift+P` is also WezTerm's
command palette, which is not passed through.

The action IDs are `alt+n` / `alt+p`, the same as OMP. The arrow ids `alt+down` /
`alt+up` match `M-n` / `M-p` only under legacy `ESC`+key encoding, via `pi-tui`'s
`LEGACY_SEQUENCE_KEY_IDS`; under kitty or modifyOtherKeys they match nothing.
The letter ids match all three encodings.

That takes `Alt+Up` from `app.message.dequeue`, which moves to `Alt+Q` — Pi's
own Windows fallback for that action, unused on macOS. It does not move back:
legacy `ESC p` carries both `alt+up` and `alt+p`.

## Ghost suggestions shadow four chords

`pi-autosuggestions` (declared in `home/.chezmoidata/plugins/pi.yaml`) draws a
zsh-autosuggestions-style ghost after the cursor. Its editor intercepts four
chords **before** delegating to the app keybindings, so while a ghost is
visible those chords do not reach the actions below:

| Keys | Assignment here | While a ghost shows |
| --- | --- | --- |
| `Alt+P` / `M-p` | Previous scoped model | Previous ghost candidate |
| `Alt+N` / `M-n` | Next scoped model | Next ghost candidate |
| `Alt+F` | Word right | Accept one ghost word |
| `Right` | Cursor right | Accept the whole ghost |

The package matches `alt+up` / `alt+down`, so this shadowing applies under legacy
encoding only.

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
| `Alt+N` | Reorder a model down (selector only) | Next scoped model; ghost candidate while one shows | **Add** |
| `Alt+P` | Dequeue a queued message | Previous scoped model; ghost candidate while one shows | **Change** |
| `Alt+Q` | No assignment on macOS (Windows: dequeue) | Dequeue a queued message | **Add** |
| `Ctrl+Alt+R` | No assignment (`Ctrl+R` renamed sessions) | Rename session | **Change** |
| `Right` | Cursor right | Accept ghost suggestion while one shows | **Add** |
| `Alt+F` | Word right | Accept one ghost word while one shows | **Change** |
| `Ctrl+Right` | No assignment | Accept one ghost word while one shows | **Add** |
| `Escape` | Abort; restore queued messages | Also dismisses the ghost | **Add** |
