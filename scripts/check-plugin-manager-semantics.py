#!/usr/bin/env python3

import json
import os
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
command = ["chezmoi"]
state = os.environ.get("CHEZMOI_VERIFY_STATE")
cache = os.environ.get("CHEZMOI_VERIFY_CACHE")
if state:
    command.extend(["--persistent-state", state])
if cache:
    command.extend(["--cache", cache])
command.extend(["data", "--source", str(root)])
data = json.loads(subprocess.check_output(command))
managers = data["plugin_managers"]
tools = data["tools"]
plugins = data["plugins"]
allowed = {"{source}", "{name}", "{installed}", "{ref_args}"}


def fail(message):
    raise SystemExit("plugin manager semantics: " + message)


for name, manager in managers.items():
    if name not in tools:
        fail(f"unknown tool {name!r}")
    if name not in plugins:
        fail(f"{name}: missing plugins.{name} declaration")
    if manager.get("identity_transform") == "npm_name":
        if manager["identity"] != "source":
            fail(f"{name}: npm_name identity transform requires identity: source")
        sources = [
            provider.get("source", "")
            for provider in plugins[name].get("providers", [])
        ]
        sources.extend(
            provider.get("sources", {}).get(name, "")
            for provider in plugins.get("providers", [])
            if name in provider.get("sources", {})
        )
        bad_sources = [source for source in sources if not source.startswith("npm:")]
        if bad_sources:
            fail(f"{name}: npm identities require npm: sources: {bad_sources}")
    commands = [manager["install"], manager["uninstall"]]
    if manager.get("enable"):
        commands.append(manager["enable"])
    marketplace = manager.get("marketplaces")
    if marketplace:
        commands.extend([marketplace["install"], marketplace["uninstall"]])
    for command in commands:
        unknown = {
            token
            for token in command
            if token.startswith("{") and token.endswith("}") and token not in allowed
        }
        if unknown:
            fail(f"{name}: unknown command placeholders {sorted(unknown)}")

scripts = root / "home/.chezmoiscripts"
fixed = {
    "run_onchange_before_190_reconcile-plugins.py.tmpl",
    "run_onchange_after_200_setup-plugins.py.tmpl",
}
actual = {
    path.relative_to(scripts).as_posix()
    for path in scripts.rglob("*plugin*.tmpl")
}
if actual != fixed:
    fail(f"plugin lifecycle scripts must be exactly {sorted(fixed)}, got {sorted(actual)}")

print("ok plugin manager semantics")
