#!/bin/zsh

SYSTEM=$(detect_os)

if [ "$SYSTEM" = "termux" ]; then
    if [ ! -d "$HOME/storage" ]; then
        termux-setup-storage
    fi
fi
