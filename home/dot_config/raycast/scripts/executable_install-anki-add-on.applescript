#!/usr/bin/osascript

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Install Anki Add-on
# @raycast.mode compact

# Optional parameters:
# @raycast.icon 📥
# @raycast.argument1 { "type": "text", "placeholder": "Add-on Codes" }

# Documentation:
# @raycast.description Install Anki's Add-on with given codes
# @raycast.author Misaka
# @raycast.authorURL https://github.com/chuxubank

on run argv
    -- Get the first argument (a single string of add-on codes separated by commas)
    set rawCodes to item 1 of argv

    -- Convert the string into a list of codes (split by commas)
    set AppleScript's text item delimiters to ","
    set addonCodes to text items of rawCodes
    set AppleScript's text item delimiters to "" -- Reset delimiters

    -- Launch Anki if it's not already running
    tell application "Anki" to activate

    -- Wait until Anki is fully opened
    delay 2

    tell application "System Events"
        -- Select the Anki window
        tell process "Anki"
            -- Open the Add-ons window using Cmd+Shift+A
            -- keystroke "a" using {command down, shift down}
            click menu item "Add-ons" of menu "Tools" of menu bar 1

            -- Loop through each add-on code
            repeat with addonCode in addonCodes

                -- Wait for the Add-ons window to open
                delay 1

                -- Click on "Get Add-ons" button
                click button "Get Add-ons..." of window "Add-ons"

                -- Wait for the "Install Add-on" dialog
                delay 1

                -- Enter the current add-on code from the list
                keystroke addonCode

                -- Press the "Return" key to install the add-on
                keystroke return

                -- Wait for the installation process to complete (adjust this delay if needed)
                delay 5

                -- Close the Install Add-on window
                keystroke return
            end repeat
        end tell
    end tell
end run
