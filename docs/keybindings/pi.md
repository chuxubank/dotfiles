# Pi keybindings

Source configuration:
`home/dot_pi/private_agent/modify_keybindings.json`

Current Emacs chords are in the [shared bindings](agents.md). Pi is an
in-pane application. The upstream default list is in Pi's
[keybindings.md](https://github.com/earendil-works/pi-coding-agent/blob/main/docs/keybindings.md).
After editing, run `/reload` in Pi.

`Ctrl+P` / `Ctrl+N` use `tui.editor.historyPrevious` / `historyNext`.

## Deltas from upstream

| Keys | Pi default | Current assignment | Status |
| --- | --- | --- | --- |
| `Ctrl+P` | Cycle to the next scoped model | Previous prompt history | **Change** |
| `Ctrl+N` | No editor history binding | Next prompt history | **Add** |
| `Ctrl+H` | No delete-backward binding | Delete character backward | **Add** |
| `Ctrl+R` | Rename session | Reverse-search prompt history | **Change** |
| `Ctrl+Alt+R` | No assignment (`Ctrl+R` renamed sessions) | Rename session | **Change** |
| `Ctrl+Alt+P` | No assignment (`Ctrl+P` cycled models) | Next scoped model | **Change** |
| `Ctrl+Alt+N` | No assignment (`Ctrl+Shift+P` cycled backward) | Previous scoped model | **Change** |
