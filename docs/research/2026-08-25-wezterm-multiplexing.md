# WezTerm multiplexing versus this repo's Herdr/Zellij setup

**Date:** 2026-08-25
**Scope:** Official WezTerm documentation and the official [`wezterm/wezterm`](https://github.com/wezterm/wezterm) repository only. The comparison baseline is this repository's current WezTerm, Herdr, Zellij, workspace, and plugin configuration.

## Executive conclusion

**WezTerm can replace most of Zellij's basic local mux role when the client is always WezTerm, but it cannot replace Herdr.** Its native mux already covers windows, tabs, panes, named workspaces, detach/reattach through a Unix-domain mux server, SSH/TLS domains, remote spawning, Lua/CLI control, startup layouts, pane movement, copy/search/scrollback, status/tab bars, desktop notifications, and multiple attached clients. The core data model is explicitly windows → tabs → panes grouped into workspaces ([mux API](https://wezterm.org/config/lua/wezterm.mux/index.html), [workspaces](https://wezterm.org/recipes/workspaces.html)).

The important gaps are:

1. WezTerm's own documentation still calls multiplexing **“a young feature”**, and the installed CLI labels `wezterm cli` as interacting with an **experimental mux server** ([multiplexing overview](https://wezterm.org/multiplexing.html)).
2. Persistence is **process lifetime**, not session resurrection: a standalone mux daemon can survive GUI detach/reconnect, but there is no built-in snapshot/save/restore across mux-server exit or reboot. The upstream save-layout request remains open ([issue #3237](https://github.com/wezterm/wezterm/issues/3237)).
3. WezTerm has generic Lua events, process inspection, user variables, text injection, and notifications, but no built-in coding-agent registry, state hooks, orchestration, pairing, or worktree lifecycle. Those are the parts Herdr provides in this repo.
4. A WezTerm mux is a WezTerm-specific domain, whereas Zellij remains usable from Ghostty, SSH terminals, or other terminal emulators. Replacing Zellij would therefore trade terminal independence for tighter native-GUI integration.

**Recommendation:** keep Herdr. Keep Zellij as the portable/default mux for Ghostty and remote or terminal-independent workflows. If reducing duplication is valuable, pilot WezTerm's Unix-domain mux as an **optional WezTerm-native replacement for Zellij**, not as an immediate repo-wide replacement.

## Installed-version applicability

Local commands report:

```text
wezterm 20240203-110809-5046fc22
wezterm-mux-server 20240203-110809-5046fc22
```

That build is also the latest published stable GitHub release as of this report ([official release](https://github.com/wezterm/wezterm/releases/tag/20240203-110809-5046fc22)). The documentation website follows the development branch and sometimes marks functionality as `nightly`; this report treats a feature as available locally only when it is documented with a `Since` version no newer than `20240203-110809-5046fc22`, is present in the installed CLI help, or is present in the corresponding stable source tag.

All core capabilities recommended below meet that test, including SSH domains (since `20230408`), Lua mux/startup APIs (since `20220624`), workspaces (since `20220319`), pane relocation (since `20230326`), plugins (since `20230320`), and multi-client listing (since `20220624`). Nightly-only refinements are not relied upon.

The repo briefly enabled a local `unix` domain as the default GUI startup
target during the pilot, then disabled it again. The current configuration
uses the normal GUI-local mux startup, still discovers `SSH:` and `SSHMUX:`
domains from `~/.ssh/config`, and maximizes windows at `gui-startup`. TLS
domains remain unconfigured.

## Capability matrix

Legend:

- **Replace** — sufficient to replace this portion of the current tool's role.
- **Partial** — technically covers the base behavior, but misses an important current feature or changes the operating model.
- **No** — no corresponding built-in capability.

| Capability | WezTerm built-in status on installed stable | Replace Zellij? | Replace Herdr? | Assessment |
|---|---|---:|---:|---|
| Windows, tabs, panes | **Stable/documented.** Native mux hierarchy with split, focus, resize, zoom, titles, and spawn APIs ([mux API](https://wezterm.org/config/lua/wezterm.mux/index.html), [`pane:split`](https://wezterm.org/config/lua/pane/split.html)). | **Replace** | **Partial** | Covers Herdr's visual container layer, not agent semantics. |
| Named workspaces | **Stable/documented.** A workspace labels a set of mux windows; the GUI displays windows from its active workspace ([workspace model](https://wezterm.org/recipes/workspaces.html), [`SwitchToWorkspace`](https://wezterm.org/config/lua/keyassignment/SwitchToWorkspace.html)). | **Replace** | **Partial** | Good match for Herdr workspace navigation, but workspaces are labels/groups rather than agent projects. |
| Local mux server | **Documented but mux is globally described as young.** `wezterm-mux-server --daemonize` plus a Unix domain provides a server independent of GUI windows ([Unix domains](https://wezterm.org/multiplexing.html#unix-domains)). | **Replace** | **Partial** | Replaces detach/reattach mechanics only. |
| Unix-domain attachment | **Stable/documented.** `unix_domains` can auto-start a server; `wezterm connect NAME` attaches, and `default_gui_startup_args` can make that the normal startup path ([Unix domains](https://wezterm.org/multiplexing.html#unix-domains), [`unix_domains`](https://wezterm.org/config/lua/config/unix_domains.html)). | **Replace** | **Partial** | Native WezTerm client only; not a general terminal protocol. |
| SSH domains | **Stable/documented since `20230408`.** Starts/connects to a compatible remote WezTerm mux over SSH; default SSH config produces `SSHMUX:` domains ([SSH domains](https://wezterm.org/multiplexing.html#ssh-domains), [`ssh_domains`](https://wezterm.org/config/lua/config/ssh_domains.html)). | **Partial** | **Partial** | Strong remote mux, but remote WezTerm must be installed and version-compatible. Automatic interruption recovery is not documented as strongly as TLS. |
| TLS domains | **Stable/documented.** TLS client/server domains support certificate bootstrapping; the client explicitly auto-reconnects after interruption and resumes the remote session ([TLS domains](https://wezterm.org/multiplexing.html#tls-domains), [`tls_clients`](https://wezterm.org/config/lua/config/tls_clients.html), [`tls_servers`](https://wezterm.org/config/lua/config/tls_servers.html)). | **Replace** | **Partial** | Most complete documented remote reconnect story, at the cost of server/TLS setup. |
| Persistent/reconnectable sessions | **Partial.** Local/remote mux processes and panes survive GUI disconnect while the mux server remains alive; TLS reconnect is explicit. No persistence after mux-server termination or host reboot ([multiplexing](https://wezterm.org/multiplexing.html), [issue #3237](https://github.com/wezterm/wezterm/issues/3237)). | **Partial** | **Partial** | Comparable to detach/attach, not to disk-backed restoration. |
| Remote spawning | **Stable/documented.** Spawn into a named domain with Lua or `wezterm cli spawn --domain-name`, including `SSHMUX:` domains ([SSH domain example](https://wezterm.org/multiplexing.html#ssh-domains), [`cli spawn`](https://wezterm.org/cli/cli/spawn.html), [`mux.spawn_window`](https://wezterm.org/config/lua/wezterm.mux/spawn_window.html)). | **Replace** | **Partial** | Can start commands remotely, but does not model an “agent” or its lifecycle. |
| Lua control | **Stable/documented.** Enumerate domains/windows/workspaces; get panes/tabs/windows; spawn, split, activate, rename, move, title, resize, rotate, and send text ([mux API](https://wezterm.org/config/lua/wezterm.mux/index.html), [MuxTab API](https://wezterm.org/config/lua/MuxTab/index.html), [Pane API](https://wezterm.org/config/lua/pane/index.html)). | **Replace** | **Partial** | Enough to recreate current declared layouts and custom commands in Lua. |
| CLI control | **Stable, but CLI describes the mux interface as experimental.** List clients/windows/tabs/panes; spawn/split; activate/resize/zoom/kill panes; send/get text; move pane to a tab; rename workspace; set titles ([CLI index](https://wezterm.org/cli/cli/index.html)). | **Replace** | **Partial** | Useful automation substrate, narrower than Herdr's agent-aware CLI. |
| Layouts/startup automation | **Stable/documented.** `gui-startup` and `mux-startup` can construct windows/workspaces/tabs/panes, set CWD/env, start commands, and send initial input ([`gui-startup`](https://wezterm.org/config/lua/gui-events/gui-startup.html), [`mux-startup`](https://wezterm.org/config/lua/mux-events/mux-startup.html)). | **Replace** | **Partial** | Can port [`workspaces.yaml`](../../home/.chezmoidata/workspaces.yaml), but requires generated/handwritten Lua and lacks Herdr's live agent start/reconcile semantics. |
| Session resurrection | **No built-in stable feature.** Startup recreation exists, but save/snapshot/restore remains an open upstream request ([issue #3237](https://github.com/wezterm/wezterm/issues/3237)). | **No** | **No** | Third-party Lua may approximate layouts, but that is not a core guarantee and is outside this report's primary-source scope. |
| Pane movement | **Stable/documented.** Move a pane into a new split, tab, window, or workspace; rotate pane positions ([`cli split-pane --move-pane-id`](https://wezterm.org/cli/cli/split-pane.html), [`move-pane-to-new-tab`](https://wezterm.org/cli/cli/move-pane-to-new-tab.html), [`pane:move_to_new_tab`](https://wezterm.org/config/lua/pane/move_to_new_tab.html), [`pane:move_to_new_window`](https://wezterm.org/config/lua/pane/move_to_new_window.html)). | **Replace** | **Partial** | Covers the relevant layout mechanics. |
| Copy, scroll, search | **Stable/documented.** Native scrollback, scrollbar, copy mode, quick select, regex search overlay, selection and clipboard integration ([scrollback/search](https://wezterm.org/scrollback.html), [copy mode](https://wezterm.org/copymode.html), [quick select](https://wezterm.org/quickselect.html)). | **Replace** | **Replace** | Often better integrated than a nested TUI mux because the GUI owns rendering/clipboard. |
| Status and tab bars | **Stable/documented.** Configurable tab bar, `format-tab-title`, left/right status, titles, progress, user vars and pane metadata ([`format-tab-title`](https://wezterm.org/config/lua/window-events/format-tab-title.html), [`set_right_status`](https://wezterm.org/config/lua/window/set_right_status.html)). | **Replace** | **Partial** | Can display state supplied by scripts/agents, but does not discover Herdr agent state itself. |
| Notifications | **Stable generic primitives.** Bell events and desktop toast notifications are available ([`bell`](https://wezterm.org/config/lua/window-events/bell.html), [`toast_notification`](https://wezterm.org/config/lua/window/toast_notification.html)). | **Replace** | **Partial** | Can notify on BEL or custom events; does not replace Heeler pairing/encrypted agent-state notifications. |
| Agent awareness | **No built-in agent model.** Lua can inspect a local foreground process, but that API explicitly does not report mux/remote foreground process details; applications can publish user vars that propagate to mux clients ([process info limitations](https://wezterm.org/config/lua/pane/get_foreground_process_info.html), [`get_user_vars`](https://wezterm.org/config/lua/pane/get_user_vars.html)). | N/A | **No** | Hooks could publish custom state, but that would be a new Herdr-like integration layer. |
| Agent orchestration | **No.** Generic spawn, send/get text, events, and CLI are available, but there is no built-in task delegation, blocked/done lifecycle, agent naming, or coordinated control. | N/A | **No** | Current [`herdr-layout`](../../home/bin/executable_herdr-layout.tmpl) calls `herdr agent start`; WezTerm has no semantic equivalent. |
| Worktree management | **No.** Spawn APIs accept `cwd` and environment variables, but WezTerm does not create, track, or clean Git worktrees ([`mux.spawn_window`](https://wezterm.org/config/lua/wezterm.mux/spawn_window.html), [`pane:split`](https://wezterm.org/config/lua/pane/split.html)). | N/A | **No** | External scripts could do it, but it is outside the mux model. |
| Plugin extensibility | **Stable but configuration-oriented.** Plugins are Lua packages cloned from HTTP(S) or local Git URLs and typically expose `apply_to_config`; updates are explicit ([plugin docs](https://wezterm.org/config/plugins.html), [`wezterm.plugin.require`](https://wezterm.org/config/lua/wezterm.plugin/require.html)). | **Partial** | **No** | Useful for UI/config composition, not equivalent to Zellij's runtime WASM plugins or Herdr's agent integrations and action plugins. |
| Multi-client behavior | **Supported, lightly documented.** `list-clients` reports each client's active workspace and focused pane ([`list-clients`](https://wezterm.org/cli/cli/list-clients.html)). Stable source stores workspace/focus per client ([`ClientInfo`](https://github.com/wezterm/wezterm/blob/20240203-110809-5046fc22/mux/src/client.rs#L41-L52), [per-client workspace methods](https://github.com/wezterm/wezterm/blob/20240203-110809-5046fc22/mux/src/lib.rs#L603-L624)). | **Partial** | **Partial** | Multiple clients can attach to the same shared mux objects, with client-local active workspace/focus. There is no documented Zellij-style mirrored/non-mirrored session mode, collaboration UI, role model, or access policy. |

## What maps cleanly from the current repo

### Zellij features WezTerm can absorb

The current Zellij setup uses tabs/panes, direct and prefix navigation, split/resize/zoom, scroll/search, detach, status/tab bars, pane relocation, generated layouts, and plugins such as session/layout managers ([Zellij config](../../home/dot_config/zellij/config.kdl.tmpl), [generated default layout](../../home/dot_config/zellij/exact_layouts/default.kdl.tmpl)). WezTerm can directly absorb the **core terminal-management subset**:

- `Ctrl+1…9` tab activation and `Ctrl+;`-style leader bindings;
- pane focus, split, resize, zoom, rotate, and pane-to-tab/window moves;
- named workspaces and launcher-based workspace selection;
- scroll/copy/search using native GUI facilities;
- startup construction of the declared tabs/panes/CWDs/commands;
- detached local sessions through a daemonized Unix domain;
- remote domains through SSH or TLS;
- status/tab formatting and generic notifications.

It does **not** cleanly absorb Zellij's terminal independence, session-manager UX, runtime WASM plugin model, web client, explicit shared-session modes, or any future session-resurrection workflow.

### Herdr features WezTerm cannot absorb

The current Herdr setup is more than a mux:

- named agent creation by `kind` from the shared workspace declaration ([`workspaces.yaml`](../../home/.chezmoidata/workspaces.yaml));
- integrations installed for Codex, Claude, Grok, OpenCode and other agents ([integration setup template](../../home/.chezmoitemplates/herdr/run.py));
- agent-state hook cleanup/install lifecycle ([cleanup template](../../home/.chezmoitemplates/herdr/cleanup.py));
- Heeler pairing and encrypted blocked/done notifications, plus layout plugins ([Herdr plugin data](../../home/.chezmoidata/plugins/herdr.yaml));
- live workspace/tab/pane creation followed by `herdr agent start` and workspace focus ([`herdr-layout`](../../home/bin/executable_herdr-layout.tmpl)).

WezTerm can provide the panes in which these agents run and can display externally published status, but replacing those semantics would require building and maintaining a new orchestration layer on top of Lua, OSC user variables, CLI text injection, and external scripts. That would duplicate Herdr rather than replace it.

## Persistence and multi-client caveats

- **GUI-local tabs are not the same as a detached session.** To survive closing all GUI clients, use a separate Unix-domain `wezterm-mux-server`; otherwise the ordinary GUI process owns the local mux.
- **Daemon survival is not resurrection.** Reattachment works while the mux daemon and child processes remain alive. Restarting the daemon or host loses runtime state; startup Lua can recreate a declared layout but not restore arbitrary process state, shell history, or scrollback.
- **TLS has the strongest documented reconnect guarantee.** The official TLS flow explicitly says interrupted connections automatically reconnect and resume. Avoid assuming identical seamless recovery for SSH domains without testing the exact failure mode.
- **Multi-client state is mixed.** Active workspace and focused pane are tracked per client, but panes/tabs/windows and their processes are shared mux objects. The docs do not promise independent collaborative cursors, per-client pane geometry, locking, permissions, or Zellij's mirrored-session switch.
- **Mux APIs are powerful but not presented as fully mature.** The feature-level warning and experimental CLI wording justify a pilot before deleting Zellij configuration.

## Migration recommendation

### Recommended end state

1. **Keep Herdr unchanged** as the agent-aware workspace/orchestration layer.
2. **Keep Zellij available** for Ghostty, generic SSH, shared/portable sessions, and fallback.
3. Keep the **WezTerm-native mux profile** optional and disabled by default
   until a later pilot:
   - re-enable a named `unix_domains` entry only when local detach/reattach is
     wanted;
   - use the discovered `SSHMUX:` domains independently for compatible remote
     hosts;
   - move declared layout generation from Zellij KDL to Lua `mux-startup` or generate Lua from [`workspaces.yaml`](../../home/.chezmoidata/workspaces.yaml);
   - preserve the current terminal/mux key ownership documented in [`README.md`](../../README.md).
4. Do not remove Zellij until the pilot validates: GUI close/reattach, macOS sleep, mux-server crash behavior, upgrades/config reloads, multi-client focus behavior, SSH/TLS reconnect, long-lived scrollback memory, and the interaction with Herdr agent hooks.

### Decision by objective

| Objective | Recommendation |
|---|---|
| Eliminate nested Zellij inside WezTerm while retaining tabs/panes/workspaces | **Optional: pilot WezTerm Unix-domain mux before enabling it by default.** |
| Use one mux consistently from both WezTerm and Ghostty | **Keep Zellij.** |
| Replace remote Zellij where WezTerm is installed on both ends | **Possible:** SSH domain for convenience; TLS domain when automatic reconnect is important. |
| Restore a full session after reboot | **Do not migrate on that basis:** WezTerm lacks built-in resurrection. |
| Replace Herdr agent workspaces, integrations, notifications, and orchestration | **No. Keep Herdr.** |
| Simplify the repo with the least risk | **Keep current architecture; optionally add WezTerm mux as an opt-in profile.** |

## Bottom line

WezTerm is already a capable **terminal-native multiplexer** and can replace the everyday windows/tabs/panes/workspaces portion of Zellij for a WezTerm-only local workflow. Its Unix, SSH, and TLS domains are real detach/reattach mechanisms, not merely GUI tabs. However, the mux remains explicitly young/experimental, has no built-in session resurrection, and is tied to the WezTerm client. It should therefore be treated as a **partial Zellij replacement and a non-replacement for Herdr**.
