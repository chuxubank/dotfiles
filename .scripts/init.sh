#!/bin/sh

export SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

. "$SCRIPT_DIR/common.sh"

. "$SCRIPT_DIR/setup-zsh.sh"

exec zsh "$SCRIPT_DIR/post-init.sh"
