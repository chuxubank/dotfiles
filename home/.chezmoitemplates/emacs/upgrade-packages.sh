CI=true make -C {{ joinPath .chezmoi.homeDir .path.personal.emacs }} sync-upgrade-packages
