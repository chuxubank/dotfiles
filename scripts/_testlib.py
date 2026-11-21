#!/usr/bin/env python3
"""Render chezmoi templates for offline checks.

prefix is ordinary template text prepended to the body and must not print.
Render each case on its own; do not pack several cases into one template.
"""

import json
import os
import subprocess
from pathlib import Path


def command(root, *args):
    """chezmoi argv, including the verify state db and cache when set."""
    cmd = ["chezmoi"]
    for flag, name in (
        ("--persistent-state", "CHEZMOI_VERIFY_STATE"),
        ("--cache", "CHEZMOI_VERIFY_CACHE"),
    ):
        value = os.environ.get(name)
        if value:
            cmd.extend([flag, value])
    cmd.extend(args)
    cmd.extend(["--source", str(Path(root))])
    return cmd


def capture(root, args, *, stdin=None, env=None):
    return subprocess.run(
        command(root, *args),
        input=stdin,
        text=True,
        capture_output=True,
        env={**os.environ, **(env or {})},
        check=False,
    )


def render(root, template, *, prefix="", env=None):
    result = capture(root, ["execute-template"], stdin=prefix + template, env=env)
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return result.stdout


def context_overlay(patch=None, *, expr=None, clear=()):
    """Template text that binds $ctx to a copy of the dot with patch merged in.

    clear names top-level keys emptied before the merge. mergeOverwrite keeps
    sibling entries, so a partial tools, llm, or mcp map would otherwise
    retain the live declarations.
    """
    if (patch is None) == (expr is None):
        raise ValueError("pass exactly one of patch or expr")
    if expr is None:
        expr = json.dumps(json.dumps(patch)) + " | fromJson"
    text = "{{- $ctx := deepCopy . -}}"
    for key in clear:
        text += "{{- $_ := set $ctx %s (dict) -}}" % json.dumps(key)
    text += "{{- $ctx = mergeOverwrite $ctx (" + expr + ") -}}"
    return text
