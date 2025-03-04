#!/bin/zsh

install_package "pass"

if [ -d "$HOME/.password-store" ]; then
    echo "✅ password store dir exist."
else
    gh repo clone pass "$HOME/.password-store"
fi
