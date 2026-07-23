env -u CI TERM_PROGRAM=chezmoi make -C {{ joinPath .chezmoi.homeDir .path.personal.emacs }} sync-upgrade-packages
