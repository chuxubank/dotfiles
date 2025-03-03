#!/bin/zsh

source "$SCRIPT_DIR/common.sh"

install_package "pass"

export PASSWORD_STORE_DIR="$HOME/Developer/Personal/pass"
if [ -d "$PASSWORD_STORE_DIR" ]; then
    echo "✅ password store dir exist."
else
    gh repo clone pass "$PASSWORD_STORE_DIR"
fi

install_package "gnupg" "gpg"

if gpg --list-secret-keys | grep -q "^sec"; then
    echo "✅ gpg secret key found."
else
    echo "❌ no gpg secret key found."
    while true; do
        echo "🔑 Please enter the path to your GPG private key file: "
        read -e -p "> " key_file
        if [ -f "$key_file" ]; then
            echo "📥 Importing GPG key from $key_file..."
            gpg --import --pinentry-mode=loopback "$key_file" && echo "✅ Key imported successfully!" && break
        else
            echo "⚠️ File not found. Please enter a valid path."
        fi
    done
fi
