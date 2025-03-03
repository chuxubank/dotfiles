#!/bin/sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

source "$SCRIPT_DIR/setup-zsh.sh"

exec zsh "$SCRIPT_DIR/setup-pass.sh"
