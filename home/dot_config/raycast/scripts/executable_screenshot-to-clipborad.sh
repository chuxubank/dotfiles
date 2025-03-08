#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Phoneshot to Clipboard
# @raycast.mode compact

# Optional parameters:
# @raycast.icon 📱
# @raycast.packageName Android

# Documentation:
# @raycast.author Misaka
# @raycast.authorURL https://github.com/chuxubank

file-to-clipboard() {
    osascript \
        -e 'on run args' \
        -e 'set the clipboard to POSIX file (first item of args)' \
        -e end \
        "$@"
}

phoneshot() {
    copy_to_clipboard=0
    if [ $# -eq 0 ]
    then
        :
    else
        if [[ $1 == '-c' ]] || [[ $1 == '--copy' ]]; then
            copy_to_clipboard=1
        elif [[ $1 == '-h' ]] || [[ $1 == '--h' ]]; then
            echo 'usage: '
            echo 'phoneshot/pshot     将手机截屏并保存为 ~/Downlodas/screenshots.png'
            echo 'phoneshot/pshot -c  将手机截屏并保存，然后复制图片到剪贴板'
            return
        fi
    fi

    name="phoneshot.png"
    adb shell screencap -p /sdcard/$name
    out_file=~/Downloads/$name
    adb pull /sdcard/$name $out_file
    adb shell rm /sdcard/$name
    echo "save phone screenshot to $out_file"

    if [[ $copy_to_clipboard == 1 ]]; then
        file-to-clipboard $out_file
        echo "copy phone screenshot file to clipboard"
    fi
}

phoneshot -c
