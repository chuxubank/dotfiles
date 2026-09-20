# Zsh and fzf-tab

Source configuration: `home/dot_zshrc.tmpl`

fzf-tab is enabled through `home/.chezmoidata/tools.yaml`. It replaces only
Zsh's native completion-selection menu; it does not wrap the shell in another
PTY. The plugin loads after oh-my-zsh initializes `compinit` and before
`zsh-autosuggestions` and `zsh-syntax-highlighting`, as required upstream.

## Completion bindings

| Keys | fzf-tab default | Current assignment | Status |
| --- | --- | --- | --- |
| `Tab` | Open fzf-tab for the current Zsh completion, then accept the selected candidate | Same | **Change** from the standard Zsh completion menu |
| `Ctrl+Space` | Select multiple candidates | Same | Unchanged |
| `F1` / `F2` | Select the previous/next completion group | No fzf-tab assignment | **Delete** |
| `<` / `>` | No fzf-tab assignment | Select the previous/next completion group | **Add** |
| `/` | Trigger continuous completion for deep paths | Same | Unchanged |

The `<` and `>` assignments apply only while the fzf-tab menu is open. During
ordinary ZLE editing they continue to insert literal characters.

fzf-tab also provides `disable-fzf-tab`, `enable-fzf-tab`, and
`toggle-fzf-tab` commands for temporarily switching back to the standard Zsh
completion interface.

## Carapace interaction

Carapace is configured as an optional completion provider but is disabled by
default. When enabled, it registers its completion specs after `compinit` and
before fzf-tab, so fzf-tab remains the menu UI. Its fallback bridges are
limited to `zsh,fish,bash`; the inshellisense bridge is deliberately excluded.
Carapace adds completion candidates and does not add a separate keybinding.
