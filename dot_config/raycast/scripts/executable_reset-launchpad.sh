#!/bin/zsh

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Reset Launchpad
# @raycast.mode compact

# Optional parameters:
# @raycast.icon 🚀
# @raycast.packageName UI

# Documentation:
# @raycast.author Misaka
# @raycast.authorURL https://github.com/chuxubank

defaults write com.apple.dock ResetLaunchPad -bool true && killall Dock
