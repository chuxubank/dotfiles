#!/bin/sh

if [ -d "$HOME/.oh-my-zsh" ]; then
    echo "OMZ installed"
else
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
fi

if type pass >/dev/null 2>&1; then
    echo "Pass installed"
else
    case "$(uname -s)" in
    Darwin)
        brew install pass
        ;;
    Linux)
        # Add installation commands for Linux here
        ;;
    *)
        echo "Unsupported OS"
        exit 1
        ;;
    esac
fi

# Check if the pass repository is already cloned
export PASSWORD_STORE_DIR="$HOME/Developer/Personal/pass"
if [ -d "$PASSWORD_STORE_DIR" ]; then
    echo "Pass dir exist"
else
    gh repo clone pass "$PASSWORD_STORE_DIR"
fi
