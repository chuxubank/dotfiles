# Kill existing Emacs session if running
\emacsclient --eval '(kill-emacs)' >/dev/null 2>&1 || true

# Start Emacs depending on OS
{{ if eq .chezmoi.os "android" -}}
termux-x11 :1 -xstartup "\emacs" &
{{ else -}}
if \emacs --version 2>&1 | \grep -q 'Emacs Mac Port'; then
    \emacs &
else
    \emacsclient -cn -a=""
fi
{{ end -}}
