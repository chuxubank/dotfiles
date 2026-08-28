# Repository instructions

## Keyboard documentation

When changing keyboard shortcuts in the Ghostty, WezTerm, Herdr, or Zellij
configuration, update the summary in `README.org` and the matching detailed
reference in `docs/keybindings/` in the same change. Include both the tool
default and the current assignment, and mark deliberate changes prominently.
Treat the configuration files as the source of truth and keep the summary
concise.

Run `make verify` after modifying keyboard configuration or its documentation.
