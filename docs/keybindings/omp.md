# OMP keybindings

Source configuration:
`home/dot_omp/private_agent/modify_keybindings.yml`

Current Emacs chords are in the [shared bindings](agents.md). OMP is an
in-pane application. User remaps live in `~/.omp/agent/keybindings.yml`.
The upstream default list is in OMP's
[keybindings.md](https://github.com/can1357/oh-my-pi/blob/main/docs/keybindings.md).
After editing, restart OMP or run `/hotkeys` to inspect the active chords.

OMP has no `tui.editor.historyPrevious` / `historyNext` actions. `Ctrl+P` /
`Ctrl+N` are added to `cursorUp` / `cursorDown`. Double `Ctrl+C` still exits
(clear editor first, exit second). Session-picker `app.session.delete` is
unchanged.

## Deltas from upstream

| Keys | OMP default | Current assignment | Status |
| --- | --- | --- | --- |
| `Ctrl+P` | Cycle to the next scoped model | Previous line / prompt history | **Change** |
| `Ctrl+N` | No editor binding | Next line / prompt history | **Add** |
| `Ctrl+H` | No delete-backward binding | Delete character backward | **Add** |
| `Ctrl+D` | Exit (saves the current prompt as a draft) | Delete character forward | **Change** |
| `Ctrl+R` | Search prompt history (editor); rename session (picker) | Reverse-search prompt history; rename on `Ctrl+Alt+R` | **Change** |
| `Ctrl+Alt+R` | No assignment (`Ctrl+R` renamed sessions) | Rename session | **Change** |
| `Ctrl+Alt+P` | No assignment (`Ctrl+P` cycled models) | Next scoped model | **Change** |
| `Ctrl+Alt+N` | No assignment (`Ctrl+Shift+P` cycled backward) | Previous scoped model | **Change** |
