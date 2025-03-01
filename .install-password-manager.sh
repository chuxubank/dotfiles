#!/bin/sh

if [ -d "$HOME/.oh-my-zsh" ]; then
    echo "✅ OMZ installed."
else
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
fi

# Check pass
if type pass >/dev/null 2>&1; then
    echo "✅ Pass installed."
else
    case "$(uname -s)" in
    Darwin)
        brew install pass
        ;;
    Linux)
        # Add installation commands for Linux here
        ;;
    *)
        echo "❌ Unsupported OS."
        exit 1
        ;;
    esac
fi

export PASSWORD_STORE_DIR="$HOME/Developer/Personal/pass"
if [ -d "$PASSWORD_STORE_DIR" ]; then
    echo "✅ Pass dir exist."
else
    gh repo clone pass "$PASSWORD_STORE_DIR"
fi

# Check gpg
if type gpg >/dev/null 2>&1; then
    echo "✅ GPG installed."
else
    case "$(uname -s)" in
    Darwin)
        brew install gpg
        ;;
    Linux)
        # Add installation commands for Linux here
        ;;
    *)
        echo "❌ Unsupported OS."
        exit 1
        ;;
    esac
fi

if gpg --list-secret-keys | grep -q "^sec"; then
    echo "✅ GPG secret key found."
else
    echo "❌ No GPG secret key found."
    while true; do
        read -rp "🔑 Please enter the path to your GPG private key file: " key_file
        if [ -f "$key_file" ]; then
            echo "📥 Importing GPG key from $key_file..."
            gpg --import --pinentry-mode=loopback "$key_file" && echo "✅ Key imported successfully!" && break
        else
            echo "⚠️ File not found. Please enter a valid path."
        fi
    done
fi
