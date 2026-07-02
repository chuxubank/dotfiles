CI=true

yes | \emacs --fg-daemon \
    --eval '(package-install-selected-packages t)' \
    --eval '(when package-selected-packages (package-autoremove))' \
    --eval '(package-upgrade-all)' \
    --eval '(kill-emacs)'
