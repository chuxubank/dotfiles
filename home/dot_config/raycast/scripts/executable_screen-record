#!/usr/bin/osascript

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Screen Record
# @raycast.mode compact

# Optional parameters:
# @raycast.icon ⏺️

# Documentation:
# @raycast.description Record iOS screen
# @raycast.author Misaka
# @raycast.authorURL https://github.com/chuxubank

tell application "QuickTime Player"
    activate
    new movie recording
end tell

delay 1

tell application "System Events" to tell process "QuickTime Player"
    click button 2 of window 1
    click menu item 3 of menu 1 of button 2 of window 1
end tell

