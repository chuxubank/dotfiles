#!/bin/zsh

export SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

source "$SCRIPT_DIR/common.sh"

source "$SCRIPT_DIR/setup-gh.sh"

source "$SCRIPT_DIR/setup-gpg.sh"

source "$SCRIPT_DIR/setup-dir.sh"

source "$SCRIPT_DIR/setup-pass.sh"
