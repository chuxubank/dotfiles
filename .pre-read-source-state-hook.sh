#!/bin/sh

if [ -d "$HOME/.oh-my-zsh" ]; then
    echo "✅ OMZ installed."
    source $HOME/.local/share/chezmoi/.install-password-manager.sh
else
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
    exit 1
fi
