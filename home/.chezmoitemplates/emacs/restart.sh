# Kill existing Emacs session if running, without hanging apply.
if command -v timeout >/dev/null 2>&1; then
    timeout 10 \emacsclient --eval '(kill-emacs)' >/dev/null 2>&1 || true
else
    \emacsclient --eval '(kill-emacs)' >/dev/null 2>&1 &
    _emacsclient_pid=$!
    _i=0
    while [ "$_i" -lt 10 ] && kill -0 "$_emacsclient_pid" 2>/dev/null; do
        sleep 1
        _i=$((_i + 1))
    done
    if kill -0 "$_emacsclient_pid" 2>/dev/null; then
        kill "$_emacsclient_pid" 2>/dev/null || true
    else
        wait "$_emacsclient_pid" 2>/dev/null || true
    fi
    unset _emacsclient_pid _i
fi
# If kill-emacs didn't land (unresponsive daemon), drop the process.
pkill -TERM -f 'emacs --(bg-|fg-)?daemon' >/dev/null 2>&1 || true
_i=0
while [ "$_i" -lt 5 ] && pgrep -f 'emacs --(bg-|fg-)?daemon' >/dev/null 2>&1; do
    sleep 1
    _i=$((_i + 1))
done
pkill -KILL -f 'emacs --(bg-|fg-)?daemon' >/dev/null 2>&1 || true
unset _i

# Start Emacs depending on OS
{{ if eq .chezmoi.os "android" -}}
termux-x11 :1 -xstartup "\emacs" &
{{ else -}}
if \emacs --version 2>&1 | \grep -q 'Emacs Mac Port'; then
    \emacs &
else
    # emacs-nox (or any build without a window system) cannot open a
    # graphical client frame even when DISPLAY is set (e.g. box desktop).
    # --batch never has a graphic frame, so ask about the build instead.
    if \emacs -Q --batch --eval '(kill-emacs (if (or (featurep (quote x)) (featurep (quote pgtk))) 0 1))' >/dev/null 2>&1; then
        has_gui=1
    else
        has_gui=0
    fi
    start_emacs_daemon() {
        if [ -n "${SHELL:-}" ] && command -v "$SHELL" >/dev/null 2>&1 \
            && "$SHELL" -l -c 'command emacs --daemon'; then
            return 0
        fi
        command emacs --daemon
    }
    start_emacs_daemon || echo "warning: could not start emacs daemon" >&2
    # Open a client frame only for a GUI build with a usable display.
    # emacsclient -c without --display can fail with "could not get
    # terminal name" (and has segfaulted) when apply has no tty.
    if [ "$has_gui" -eq 1 ] && [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then
        if [ -n "${DISPLAY:-}" ]; then
            \emacsclient -n -e "(make-frame-on-display \"$DISPLAY\")" >/dev/null 2>&1 \
                || \emacsclient -n -c --display "$DISPLAY" >/dev/null 2>&1 \
                || echo "warning: could not open emacs client frame" >&2
        else
            \emacsclient -n -c >/dev/null 2>&1 \
                || echo "warning: could not open emacs client frame" >&2
        fi
    fi
fi
{{ end -}}
