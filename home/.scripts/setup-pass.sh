#!/bin/zsh

install_package "pass"

if [ -d "$PASSWORD_STORE_DIR" ]; then
    echo "✅ password store dir exist."
else
    gh repo clone pass "$PASSWORD_STORE_DIR"
fi
