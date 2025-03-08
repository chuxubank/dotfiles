#!/bin/zsh

install_package "gh"

if ! gh auth status >/dev/null 2>&1; then
    echo "⚠️ Not logged in. Logging into GitHub..."
    gh auth login
else
    echo "✅ Already logged in to GitHub."
fi

