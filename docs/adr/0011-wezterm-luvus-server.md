# Do not restart the Luvus server when WezTerm starts

`home/dot_config/wezterm/launch.lua.tmpl` starts `luvus` from `gui-startup` and
leaves `default_prog` empty. `luvus` detaches a session server that is meant to
keep panes after the client exits. The next WezTerm process only attaches to
that server.

On macOS the local-network decision belongs to the process that spawned the
server, and it is fixed at that start. After WezTerm exits, the server is
still running but no longer covered by that WezTerm. Panes then fail to open
on-link connections. Attaching again does not make a new decision.

Restarting the server from `gui-startup` would spawn it under the new WezTerm,
but it also destroys every pane on a cold start. That gives up the reason the
server survives the client. Do not do it. Restart the server only when those
pane connections are actually broken.
