# Kill existing Emacs session if running
\emacsclient --eval '(kill-emacs)' >/dev/null 2>&1 || true

# Start Emacs depending on OS
{{ if eq .chezmoi.os "android" -}}
termux-x11 :1 -xstartup "\emacs" &
{{ else -}}
if \emacs --version 2>&1 | \grep -q 'Emacs Mac Port'; then
    \emacs &
else
    if [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then
        \emacsclient -cn -a=""
    else
        # No display, including an interactive SSH session: a client frame
        # would open in the terminal and block. A failed daemon must not
        # abort the rest of this apply.
        \emacs --daemon || echo "warning: could not start emacs daemon" >&2
    fi
fi
{{ end -}}
