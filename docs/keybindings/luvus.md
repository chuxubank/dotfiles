# Luvus keybindings

Source configuration:
`home/private_dot_luvus/modify_config.json`

Luvus owns its own workspaces, tabs, and panes. The terminal still owns the
outer terminal window/tab layer.

Luvus rewrites `config.json` itself, so the prefix is merged in through a
modify-template rather than owning the whole file.

## Prefix

| Keys | Luvus default | Current assignment | Status |
| --- | --- | --- | --- |
| `Ctrl+Space` | Open Luvus command mode | `Ctrl+;` opens Luvus command mode | **Change** |
| `Ctrl+Space` twice | Send a literal `Ctrl+Space` to the pane | Send a literal `Ctrl+;` to the pane | **Change** |

## Prefix bindings

Press `Ctrl+;`, then press the following key:

| Keys | Luvus default | Current assignment | Status |
| --- | --- | --- | --- |
| `1…9` | Jump to tab 1–9 | Jump to tab 1–9 | Unchanged |
| `c` | Create a tab | Create a tab | Unchanged |
| `n` / `p` | Select the next/previous tab | Select the next/previous tab | Unchanged |
| `,` | Rename the tab | Rename the tab | Unchanged |
| `h/j/k/l` or arrows | Focus a pane | Focus a pane | Unchanged |
| `;` | Focus the next pane | Focus the next pane | Unchanged |
| `.` | Jump to the next blocked agent | Jump to the next blocked agent | Unchanged |
| `v` / `s` | Split right / down | Split right / down | Unchanged |
| `f` | Fork the agent session | Fork the agent session | Unchanged |
| `x` / `X` | Close the focused pane | Close the focused pane | Unchanged |
| `z` | Zoom the focused pane | Zoom the focused pane | Unchanged |
| `r` | Enter resize mode | Enter resize mode | Unchanged |
| `y` | Enter copy mode | Enter copy mode | Unchanged |
| `N` | Create a workspace | Create a workspace | Unchanged |
| `D` | Close the current workspace | Close the current workspace | Unchanged |
| `w` / `W` | Select the next/previous workspace | Select the next/previous workspace | Unchanged |
| `G` | Create a worktree | Create a worktree | Unchanged |
| `g` | Open the Git tab | Open the Git tab | Unchanged |
| `o` | Open the orchestration board | Open the orchestration board | Unchanged |
| `=` | Open Settings | Open Settings | Unchanged |
| `b` / `B` | Toggle the left/right sidebar | Toggle the left/right sidebar | Unchanged |
| `a` | Toggle the agent filter | Toggle the agent filter | Unchanged |
| `e` | Toggle the FILES dock | Toggle the FILES dock | Unchanged |
| `m` | Open the jump palette | Open the jump palette | Unchanged |
| `/` | Open the global fuzzy finder | Open the global fuzzy finder | Unchanged |
| `d` / `q` | Detach and keep the server active | Detach and keep the server active | Unchanged |

## Direct bindings

No prefix. `direct_keybindings` is empty by default in Luvus.

| Keys | Luvus default | Current assignment | Status |
| --- | --- | --- | --- |
| `Alt+1…9` | Unbound; `Prefix+Shift+1…9` jumps to workspace 1–9 | Jump to workspace 1–9 | **Add** |

This mirrors Herdr's `Alt+1…9` because Herdr, Zellij, and Luvus are one mux
layer and never run at the same time. Luvus's own default reaches the same
action through the prefix, which stays available.

Not yet live: `jump_workspace_1…9` landed upstream after the 0.13.4 release, so
the configured entries are ignored until the next version. Luvus only walks its
known command list when building direct bindings, so unknown ids are skipped
without an error and the binding starts working on upgrade. Until then, use
`Ctrl+; w` / `Ctrl+; W` or the jump palette at `Ctrl+; m`.

Luvus's internal tab shortcut is intentionally `Prefix+1…9`, matching the
Herdr/Zellij mux layer. Direct `Ctrl+1…9` remains available to pane
applications, and `Alt+1…9` selects workspaces as in Herdr.

## Terminal and mux layers

The outer terminal keeps these bindings:

- `Super+1…9`: terminal tab selection
- `Ctrl+Tab` / `Ctrl+Shift+Tab`: next/previous terminal tab

See the [shared key map](README.md) and the terminal-specific references for
the complete allocation.
