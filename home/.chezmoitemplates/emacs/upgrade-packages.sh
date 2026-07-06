CI=true make -C {{ joinPath .chezmoi.homeDir .path.emacs }} sync-packages
