if \emacs --version 2>&1 | \grep -q 'Emacs Mac Port'; then
    \emacs --fg-daemon --eval '(package-upgrade-all)' --eval '(kill-emacs)' && \emacsclient --eval '(kill-emacs)' && \emacs &
else
    \emacs --fg-daemon --eval '(package-upgrade-all)' --eval '(kill-emacs)' && \emacsclient -a '' --eval '(kill-emacs)' && \emacs --daemon
fi
