#!/bin/zsh

install_package "gnupg" "gpg"

if gpg --list-secret-keys | grep -q "^sec"; then
    echo "✅ gpg secret key found."
else
    echo "❌ no gpg secret key found."
    autoload -Uz compinit
    compinit
    while true; do
        key_file=""
        echo "🔑 Please enter the path to your GPG private key file: "
        vared -c -p "> " key_file
        key_file=${key_file/#\~/$HOME}
        if [ -f "$key_file" ]; then
            echo "📥 Importing GPG key from $key_file..."
            gpg --import "$key_file" && echo "✅ Key imported successfully!" && break
        else
            echo "⚠️ File not found. Please enter a valid path."
        fi
    done
fi
