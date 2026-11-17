#!/usr/bin/env python3

import json
import os
import subprocess
import sys
from pathlib import Path, PurePath

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


def fail(scope, message):
    raise SystemExit(f"{scope}: {message}")


def below(path, root_path):
    parts = PurePath(path).parts
    root_parts = PurePath(root_path).parts
    return parts[: len(root_parts)] == root_parts


def check_integrations():
    scope = "integration semantics"
    owners = data["integration_owners"]
    agents = data["integration_agents"]
    tools = data["tools"]

    def check_agent_paths(owner, where, declarations):
        for agent, paths in declarations.items():
            if agent not in agents:
                fail(scope, f"{owner}.{where}: unknown agent {agent!r}")
            for path in paths:
                if not below(path, agents[agent]):
                    fail(scope, f"{owner}.{where}.{agent}: {path!r} is outside {agents[agent]!r}")

    for agent in agents:
        if agent not in tools:
            fail(scope, f"agent root references unknown tool {agent!r}")

    for owner, spec in owners.items():
        if owner not in tools:
            fail(scope, f"unknown owner {owner!r}")
        lifecycle = spec["lifecycle"]
        target_names = [target["tool"] for target in spec["targets"]]
        if len(target_names) != len(set(target_names)):
            fail(scope, f"{owner}: duplicate targets")
        unknown_targets = set(target_names) - set(agents)
        if unknown_targets:
            fail(scope, f"{owner}: unknown targets {sorted(unknown_targets)}")
        for target in spec["targets"]:
            probe = target.get("installed")
            if probe and not below(probe["path"], agents[target["tool"]]):
                fail(
                    scope,
                    f"{owner}.targets.{target['tool']}.installed.path: "
                    f"{probe['path']!r} is outside {agents[target['tool']]!r}",
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
                fail(scope, f"{owner}.{field}: non-target agents {sorted(unknown)}")

        for agent, rule in lifecycle.get("post_install", {}).items():
            move = rule["move"]
            for field in ("from", "to"):
                if not below(move[field], agents[agent]):
                    fail(
                        scope,
                        f"{owner}.post_install.{agent}.{field}: "
                        f"{move[field]!r} is outside {agents[agent]!r}",
                    )

    print("ok integration semantics")


def check_plugin_managers():
    scope = "plugin manager semantics"
    managers = data["plugin_managers"]
    tools = data["tools"]
    plugins = data["plugins"]
    allowed = {"{source}", "{name}", "{installed}", "{ref_args}"}

    for name, manager in managers.items():
        if name not in tools:
            fail(scope, f"unknown tool {name!r}")
        if name not in plugins:
            fail(scope, f"{name}: missing plugins.{name} declaration")
        if manager.get("identity_transform") == "npm_name":
            if manager["identity"] != "source":
                fail(scope, f"{name}: npm_name identity transform requires identity: source")
            sources = [
                provider.get("source", "")
                for provider in plugins[name].get("providers", [])
            ]
            sources.extend(
                provider.get("sources", {}).get(name, "")
                for provider in plugins.get("providers", [])
                if name in provider.get("sources", {})
            )
            bad_sources = [
                source for source in sources if not source.startswith(("npm:", "git:"))
            ]
            if bad_sources:
                fail(scope, f"{name}: npm identities require npm: or git: sources: {bad_sources}")
        commands = [manager["uninstall"]]
        if manager.get("install"):
            commands.append(manager["install"])
        if manager.get("enable"):
            commands.append(manager["enable"])
        marketplace = manager.get("marketplaces")
        if marketplace:
            commands.extend([marketplace["install"], marketplace["uninstall"]])
        for command_args in commands:
            unknown = {
                token
                for token in command_args
                if token.startswith("{") and token.endswith("}") and token not in allowed
            }
            if unknown:
                fail(scope, f"{name}: unknown command placeholders {sorted(unknown)}")

    for name, spec in tools.items():
        steps = spec.get("plugin_upgrades", [])
        for step in steps:
            command_args = step.get("command")
            if not isinstance(command_args, list) or not command_args or not all(
                isinstance(arg, str) and arg for arg in command_args
            ):
                fail(scope, f"{name}: plugin upgrade command must be a nonempty argument list")
            binary = managers.get(name, {}).get(
                "binary", "claude" if name == "claude-code" else name
            )
            if command_args[0] != binary:
                fail(scope, f"{name}: plugin upgrade must invoke its own binary")
            expansion = step.get("for_each")
            if expansion not in (None, "enabled_plugins"):
                fail(scope, f"{name}: unsupported plugin upgrade expansion {expansion!r}")
            if ("{source}" in command_args) != (expansion == "enabled_plugins"):
                fail(scope, f"{name}: {{source}} requires enabled_plugins expansion")
            if any("{" in arg or "}" in arg for arg in command_args if arg != "{source}"):
                fail(scope, f"{name}: unknown plugin upgrade placeholder")

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
        fail(
            scope,
            f"plugin lifecycle scripts must be exactly {sorted(fixed)}, got {sorted(actual)}",
        )

    print("ok plugin manager semantics")


check_integrations()
check_plugin_managers()
