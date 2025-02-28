#!/bin/sh

# Check if pass is installed
if ! type pass >/dev/null 2>&1; then
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
if [ ! -d "$PASSWORD_STORE_DIR" ]; then
    gh repo clone pass "$PASSWORD_STORE_DIR"
fi
