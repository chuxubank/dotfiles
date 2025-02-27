#!/bin/zsh

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Emacs Client
# @raycast.mode compact

# Optional parameters:
# @raycast.icon 🐾
# @raycast.packageName Editor

# Documentation:
# @raycast.description Open Emacs Client
# @raycast.author Misaka
# @raycast.authorURL https://github.com/chuxubank

if emacsclient --eval '(> (length (frame-list)) 1)' 2>/dev/null | grep -q t; then
    osascript -e 'tell application "Emacs" to activate'
    echo "Bringing Emacs to the front..."
else
    emacsclient -cn -a=""
    echo "Starting Emacs..."
fi
