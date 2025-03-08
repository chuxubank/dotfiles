if \emacs --version 2>&1 | \grep -q 'Emacs Mac Port'; then
    \emacsclient --eval '(package-upgrade-all)' && \emacsclient --eval '(kill-emacs)' && \emacs &
else
    \emacsclient -a='' --eval '(package-upgrade-all)' && \emacsclient --eval '(kill-emacs)' && \emacs --daemon
fi
