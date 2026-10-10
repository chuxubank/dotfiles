# Kill existing Emacs session if running
\emacsclient --eval '(kill-emacs)' >/dev/null 2>&1 || true

# copilot.el (with no-littering) looks up copilot-language-server on PATH,
# then in ~/.config/emacs/.local/cache/copilot/bin. The managed copy is the
# bun global from packages/node.toml. A daemon started with a short PATH
# never sees that bin and aborts init, so link it into the cache as well.
emacs_dir="{{ joinPath .chezmoi.homeDir .path.personal.emacs }}"
export PATH="$HOME/{{ .path.tool.bun }}/bin:$HOME/.local/bin:${PATH:-}"
copilot_bin="$emacs_dir/.local/cache/copilot/bin/copilot-language-server"
if [ ! -x "$copilot_bin" ]; then
    copilot_managed=$(command -v copilot-language-server 2>/dev/null || true)
    if [ -n "$copilot_managed" ]; then
        mkdir -p "$(dirname "$copilot_bin")"
        ln -sfn "$copilot_managed" "$copilot_bin"
    else
        echo "copilot-language-server is not installed; Emacs copilot will not start" >&2
    fi
fi

# Start Emacs depending on OS
{{ if eq .chezmoi.os "android" -}}
termux-x11 :1 -xstartup "\emacs" &
{{ else -}}
if \emacs --version 2>&1 | \grep -q 'Emacs Mac Port'; then
    \emacs &
else
    if [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ] || [ -t 1 ]; then
        \emacsclient -cn -a=""
    else
        # No display and no TTY: a client frame cannot attach. A failed
        # daemon must not abort the rest of this apply.
        \emacs --daemon || echo "warning: could not start emacs daemon" >&2
    fi
fi
{{ end -}}
