CI=true

\emacs --fg-daemon --eval '(package-upgrade-all)' --eval '(kill-emacs)'

\emacsclient --eval '(kill-emacs)' || true

if \emacs --version 2>&1 | \grep -q 'Emacs Mac Port'; then
    \emacs &
else
    \emacsclient -cn -a=""
fi
