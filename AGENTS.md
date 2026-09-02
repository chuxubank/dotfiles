# Repository instructions

## Keyboard documentation

When changing keyboard shortcuts in the Ghostty, WezTerm, Herdr, or Zellij
configuration, update the terminal/mux summary in `README.org` and the
matching detailed reference in `docs/keybindings/` in the same change.
When changing Pi or OMP keybindings, update the in-pane summary in
`README.org`, the shared Emacs set in `docs/keybindings/agents/README.md`, and
the tool file (`agents/pi.md` / `agents/omp.md`). Include both the tool default
and the current assignment, and mark deliberate changes prominently. Treat the
configuration files as the source of truth and keep the summary concise.

Run `make verify` after modifying keyboard configuration or its documentation.

## External repo definitions

`home/.chezmoiexternals/` holds one file per `path` namespace in
`home/.chezmoidata/path.toml`, or one per semantic group within a namespace.
When adding a `path` key that needs a clone, put its entry in the matching
existing file rather than a new per-project one, and keep entry order aligned
with the key order in `path.toml`. `darwin.toml.tmpl` (platform gate) and
`zotero.toml.tmpl` (application plugins) are outside the scheme. The rationale
and the rejected `[path.sideline]` alternative are in
`docs/adr/0004-externals-per-path-namespace.md`.

Private or host-specific entries need a CI guard, either `ne .host_env "ci"` in
the file or a covering rule in `.chezmoiignore`; moving an entry between files
can drop the guard it was relying on. `common.toml.tmpl` has neither on purpose,
because `llm/tool-config` reads its `path.cache` fetches at render time on every
host. chezmoi merges all externals into one namespace and a duplicated path is
silently last-wins, so verify no path is defined twice after moving entries.
