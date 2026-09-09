#!/usr/bin/env python3

import json
import os
import subprocess
import sys
from pathlib import PurePath

root = sys.argv[1]
command = ["chezmoi"]
state = os.environ.get("CHEZMOI_VERIFY_STATE")
cache = os.environ.get("CHEZMOI_VERIFY_CACHE")
if state:
    command.extend(["--persistent-state", state])
if cache:
    command.extend(["--cache", cache])
command.extend(["data", "--source", root])
data = json.loads(subprocess.check_output(command))
owners = data["integration_owners"]
agents = data["integration_agents"]
tools = data["tools"]


def fail(message):
    raise SystemExit("integration semantics: " + message)


def below(path, root_path):
    parts = PurePath(path).parts
    root_parts = PurePath(root_path).parts
    return parts[: len(root_parts)] == root_parts


def check_agent_paths(owner, where, declarations):
    for agent, paths in declarations.items():
        if agent not in agents:
            fail(f"{owner}.{where}: unknown agent {agent!r}")
        for path in paths:
            if not below(path, agents[agent]):
                fail(f"{owner}.{where}.{agent}: {path!r} is outside {agents[agent]!r}")


for agent in agents:
    if agent not in tools:
        fail(f"agent root references unknown tool {agent!r}")

for owner, spec in owners.items():
    if owner not in tools:
        fail(f"unknown owner {owner!r}")
    lifecycle = spec["lifecycle"]
    target_names = [target["tool"] for target in spec["targets"]]
    if len(target_names) != len(set(target_names)):
        fail(f"{owner}: duplicate targets")
    unknown_targets = set(target_names) - set(agents)
    if unknown_targets:
        fail(f"{owner}: unknown targets {sorted(unknown_targets)}")
    for target in spec["targets"]:
        probe = target.get("installed")
        if probe and not below(probe["path"], agents[target["tool"]]):
            fail(
                f"{owner}.targets.{target['tool']}.installed.path: "
                f"{probe['path']!r} is outside {agents[target['tool']]!r}"
            )

    cleanup = lifecycle.get("cleanup", {})
    for field in ("standalone", "json_hooks"):
        check_agent_paths(owner, f"cleanup.{field}", cleanup.get(field, {}))
    markdown = cleanup.get("markdown_refs", {})
    check_agent_paths(owner, "cleanup.markdown_refs", markdown.get("agents", {}))
    marked = cleanup.get("marked_files", {})
    check_agent_paths(
        owner,
        "cleanup.marked_files",
        {agent: [rule["path"] for rule in rules] for agent, rules in marked.items()},
    )

    for field in ("target_env", "post_install"):
        unknown = set(lifecycle.get(field, {})) - set(target_names)
        if unknown:
            fail(f"{owner}.{field}: non-target agents {sorted(unknown)}")

    for agent, rule in lifecycle.get("post_install", {}).items():
        move = rule["move"]
        for field in ("from", "to"):
            if not below(move[field], agents[agent]):
                fail(
                    f"{owner}.post_install.{agent}.{field}: "
                    f"{move[field]!r} is outside {agents[agent]!r}"
                )

print("ok integration semantics")
