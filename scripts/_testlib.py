#!/usr/bin/env python3
"""Render one chezmoi template for an offline check.

prefix is ordinary template text prepended to the body and must not print.
Render each case on its own; do not pack several cases into one template.
"""

import os
import subprocess
from pathlib import Path


def render(root, template, *, prefix="", env=None):
    command = ["chezmoi"]
    for flag, name in (
        ("--persistent-state", "CHEZMOI_VERIFY_STATE"),
        ("--cache", "CHEZMOI_VERIFY_CACHE"),
    ):
        value = os.environ.get(name)
        if value:
            command.extend([flag, value])
    command.extend(["execute-template", "--source", str(Path(root))])
    result = subprocess.run(
        command,
        input=prefix + template,
        text=True,
        capture_output=True,
        env={**os.environ, **(env or {})},
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return result.stdout
