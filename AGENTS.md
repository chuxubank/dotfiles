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

`home/.chezmoidata/path.toml` owns path strings only.
`home/.chezmoidata/repositories.yaml` maps those paths to git clone metadata;
add every managed git repository there rather than writing another external
template. `home/.chezmoiexternals/repositories.toml.tmpl` is the single
renderer. Keep entries in `path.toml` namespace/key order. Platform-, app-, or
file-specific non-git externals remain in their existing specialized files.
The rationale is in
`docs/adr/0004-repository-metadata.md`.

Private or host-specific repositories need a `when` condition that excludes
inapplicable hosts. The renderer uses the shared host-condition evaluator, so
use the same `when.enabled` / `when.disabled` schema as other data files.
chezmoi merges all externals into one namespace and a duplicated destination
is silently last-wins, so verify the rendered destinations are unique.
