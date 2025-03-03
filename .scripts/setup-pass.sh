#!/bin/zsh

install_package "pass"

export PASSWORD_STORE_DIR="$HOME/Developer/Personal/pass"
if [ -d "$PASSWORD_STORE_DIR" ]; then
    echo "✅ password store dir exist."
else
    gh repo clone pass "$PASSWORD_STORE_DIR"
fi
