# Kill existing Emacs session if running
\emacsclient --eval '(kill-emacs)' >/dev/null 2>&1 || true

# Start Emacs depending on OS
{{ if eq .chezmoi.os "android" -}}
termux-x11 :1 -xstartup "\emacs" &
{{ else -}}
if \emacs --version 2>&1 | \grep -q 'Emacs Mac Port'; then
    \emacs &
else
    # emacs-nox (or any build without a window system) cannot open a
    # graphical client frame even when DISPLAY is set (e.g. box desktop).
    if \emacs -Q --batch --eval '(kill-emacs (if (display-graphic-p) 0 1))' >/dev/null 2>&1; then
        has_gui=1
    else
        has_gui=0
    fi
    if [ "$has_gui" -eq 1 ] && [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then
        \emacsclient -cn -a="" || echo "warning: could not open emacs client frame" >&2
    else
        # No usable display: a client frame would open in the terminal and
        # block. A failed daemon must not abort the rest of this apply.
        \emacs --daemon || echo "warning: could not start emacs daemon" >&2
    fi
fi
{{ end -}}
