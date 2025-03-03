#!/bin/sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/common.sh"

install_package "zsh"

if [ -d "$HOME/.oh-my-zsh" ]; then
    echo "✅ omz is already installed."
else
    echo "🚀 Installing omz..."
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
    echo "✅ omz installed!"
fi

current_shell=$(basename "$SHELL")

if [[ "$current_shell" == "zsh" ]]; then
    echo "✅ Already using zsh as the default shell."
else
    chsh -s $(command -v zsh)
    echo "✅ Switched default shell to zsh."
fi
