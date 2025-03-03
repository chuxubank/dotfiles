#!/bin/sh

detect_os() {
    OS=$(uname -s)
    case "$OS" in
        Linux)
            if [ -n "$TERMUX_VERSION" ]; then
                echo "termux"
            else
                echo "linux"
            fi
            ;;
        Darwin)
            echo "macos"
            ;;
        CYGWIN*|MINGW*|MSYS*)
            echo "windows"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

get_package_name() {
    PACKAGE=$1
    SYSTEM=$(detect_os)

    declare -A APT_MAP
    declare -A DNF_MAP
    declare -A PACMAN_MAP
    declare -A BREW_MAP

    # APT (Debian/Ubuntu)

    # DNF (RedHat/CentOS/Fedora)
    DNF_MAP["gnupg"]="gnupg2"

    # PACMAN (Arch)

    # Homebrew (macOS)

    case "$SYSTEM" in
        termux)
            echo "$PACKAGE"
            ;;
        linux)
            if type apt >/dev/null 2>&1; then
                echo "${APT_MAP[$PACKAGE]:-$PACKAGE}"
            elif type dnf >/dev/null 2>&1; then
                echo "${DNF_MAP[$PACKAGE]:-$PACKAGE}"
            elif type pacman >/dev/null 2>&1; then
                echo "${PACMAN_MAP[$PACKAGE]:-$PACKAGE}"
            else
                echo "$PACKAGE"
            fi
            ;;
        macos)
            echo "${BREW_MAP[$PACKAGE]:-$PACKAGE}"
            ;;
        windows)
            echo "$PACKAGE"
            ;;
        *)
            echo "$PACKAGE"
            ;;
    esac
}

install_package() {
    PACKAGE=$1
    EXECUTABLE=${2:-$PACKAGE}
    SYSTEM=$(detect_os)

    if type "$EXECUTABLE" >/dev/null 2>&1; then
        echo "✅ $PACKAGE is already installed."
        return 0
    fi

    PACKAGE_NAME=$(get_package_name "$PACKAGE")
    if [ $? -ne 0 ]; then
        echo "⚠️ Unable to determine package name for $PACKAGE on $SYSTEM."
        return 1
    fi

    echo "🚀 Installing $PACKAGE_NAME on $SYSTEM..."

    case "$SYSTEM" in
        termux)
            pkg update && pkg install -y "$PACKAGE_NAME"
            ;;
        linux)
            if type apt >/dev/null 2>&1; then
                sudo apt update && sudo apt install -y "$PACKAGE_NAME"
            elif type dnf >/dev/null 2>&1; then
                sudo dnf install -y "$PACKAGE_NAME"
            elif type pacman >/dev/null 2>&1; then
                sudo pacman -Syu --noconfirm "$PACKAGE_NAME"
            else
                echo "⚠️ Unsupported Linux distribution. Install $PACKAGE_NAME manually."
                return 1
            fi
            ;;
        macos)
            brew install "$PACKAGE_NAME"
            ;;
        windows)
            echo "⚠️ Please install $PACKAGE_NAME manually on Windows."
            return 1
            ;;
        *)
            echo "⚠️ Unknown system. Install $PACKAGE_NAME manually."
            return 1
            ;;
    esac

    echo "✅ $PACKAGE_NAME installation completed!"
}
