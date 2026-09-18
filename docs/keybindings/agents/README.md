# In-pane agent keybindings

Agents run inside a mux pane and share one Emacs editor chord set. This page is
the current assignment for that shared set. Per-agent defaults, and the few
implementation differences that force a chord apart, live in the tool files:

- [Pi](pi.md)
- [OMP](omp.md)

Source configurations:

- `home/dot_pi/private_agent/modify_keybindings.json`
- `home/dot_omp/private_agent/modify_keybindings.yml`

WezTerm's default `Ctrl+R` reload is unbound so the key reaches the agent;
`Super+R` and `Ctrl+Shift+R` still reload WezTerm.

Model cycle uses `Alt+N` / `Alt+P` — the Emacs next/previous pair — rather than
`Ctrl+Shift+P` / `Ctrl+Shift+N`. This keeps the modifier hierarchy consistent:
Ctrl moves by character and line (`Ctrl+N` / `Ctrl+P`), Meta moves by the larger
unit, exactly as `Ctrl+F` is a character and `Alt+F` a word.

`Ctrl+Shift+P` is additionally WezTerm's command palette and `Ctrl+Shift+N` its
new window; neither is passed through. Upstream Pi also falls back to `Alt+P` on
Windows.

Note that a Luvus pane does carry the kitty keyboard protocol — measured by
pushing flags with `CSI > 7 u` and reading back `CSI ? 7 u` — so `Ctrl+Shift+P`
would in fact arrive intact as `shift+ctrl+p`. The Alt chords are a hierarchy and
terminal-ownership choice, not a workaround for lost encoding.

The chords are letters because OMP matches only `alt+<letter>` and
`alt+shift+<letter>`. A rebound `alt+<symbol>` such as `alt+.` is accepted by
the config parser and listed by `/hotkeys`, but never fires.

Both agents use the same action IDs, `alt+n` / `alt+p`. Pi's config used the
arrow ids `alt+down` / `alt+up` until they turned out to match only under legacy
encoding; see [Pi](pi.md).

Both agents open the model selector with `Alt+M`. Pi's upstream default for
`app.model.select` is `Ctrl+L`; the current assignment deliberately replaces it.
`Alt+P` is OMP's own `app.model.selectTemporary` by default, moved to
`Alt+Shift+M` beside the shared selector chord. In Pi, `Alt+Up` is
`app.message.dequeue`, moved to `Alt+Q` — Pi's own Windows fallback for it.

Because `Ctrl+Shift+P` cannot reach the agent, WezTerm keeps its own command
palette on it; `Super+Shift+P` is a second palette chord.

`Ctrl+P` in `/resume` still toggles path display. History bindings only
override model cycling while the main editor is focused.

`/tree` filter modes use `Alt+D/T/U/L/A` rather than Pi's `Ctrl+D/T/U/L/A`
defaults. The letters are the same mnemonic (default, no-tools, user-only,
labeled-only, all); the modifier is Meta because Ctrl stays on the Emacs
editor set (`Ctrl+A/D/U`) and thinking toggle (`Ctrl+T`). OMP hardcodes the
Alt chords in the overlay and does not expose filter action ids, so Alt is
the only shared assignment the config can reach. `Ctrl+O` / `Ctrl+Shift+O`
still cycle the filter on both agents.

## Emacs editor

| Keys | Current assignment |
| --- | --- |
| `Ctrl+P` / `Ctrl+N` | Previous / next line, or prompt history when the editor is empty |
| `Ctrl+B` / `Ctrl+F` | Cursor left / right |
| `Alt+B` / `Alt+F` | Word left / right (Pi: `Alt+F` accepts a ghost word instead while one shows) |
| `Ctrl+A` / `Ctrl+E` | Line start / end |
| `Ctrl+H` / `Ctrl+D` | Delete character backward / forward |
| `Ctrl+K` / `Ctrl+U` | Delete to line end / start |
| `Ctrl+Y` / `Alt+Y` | Yank / yank-pop |
| `Ctrl+J` / `Shift+Enter` | New line |

## Prompt history and sessions

| Keys | Current assignment |
| --- | --- |
| `Ctrl+R` | Reverse-search prompt history |
| `Ctrl+Alt+R` | Rename session |

## Model cycle

| Keys | Current assignment |
| --- | --- |
| `Alt+N` | Next scoped model |
| `Alt+P` | Previous scoped model |
| `Alt+M` | Open the model selector |
| `Alt+Shift+M` | Pick a temporary model (OMP) |
| `Alt+Q` | Dequeue a queued message (Pi; was `Alt+Up`) |

In Pi these four chords are shadowed while a `pi-autosuggestions` ghost is
visible at the line end, in prose as well as in `!` bash mode. See
[Pi](pi.md#ghost-suggestions-shadow-four-chords).

## Session tree (`/tree`)

| Keys | Current assignment |
| --- | --- |
| `Alt+D` | Default tree filter |
| `Alt+T` | Hide tool results |
| `Alt+U` | User messages only |
| `Alt+L` | Labeled entries only |
| `Alt+A` | All entries |
| `Ctrl+O` / `Ctrl+Shift+O` | Cycle tree filter forward / backward |

## Message queue (Pi)

| Keys | Current assignment |
| --- | --- |
| `Enter` | Submit; while working, steer |
| `Alt+Enter` | While working, follow-up |
