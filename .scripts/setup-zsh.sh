#!/bin/sh

install_package "zsh"
install_package "git"

if [ -d "$HOME/.oh-my-zsh" ]; then
    echo "✅ omz is already installed."
else
    echo "🚀 Installing omz..."
    RUNZSH=no
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" && echo "✅ omz installed!"
fi
