#!/usr/bin/env python3

import json
import os
import re
import subprocess
import sys
from pathlib import PurePath, PureWindowsPath

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
owners = data.get("integration_owners", {})
agents = data.get("integration_agents", {})
tools = data.get("tools", {})

LIFECYCLE_KEYS = {
    "binary",
    "cleanup",
    "install",
    "label",
    "os",
    "post_install",
    "setup",
    "skip_errors",
    "target_env",
    "timeout_seconds",
    "uninstall",
    "uninstall_all",
    "uninstall_disabled",
}
CLEANUP_KEYS = {
    "command_exact",
    "command_fields",
    "command_prefixes",
    "extras",
    "json_hooks",
    "managed_blocks",
    "markdown_refs",
    "marked_files",
    "needles",
    "standalone",
}
SUPPORTED_OS = {"android", "darwin", "linux", "windows"}


def fail(message):
    raise SystemExit("integration schema: " + message)


def mapping(value, where):
    if not isinstance(value, dict):
        fail(f"{where} must be a map")
    return value


def string_list(value, where, allow_empty=False):
    if not isinstance(value, list) or (not allow_empty and not value):
        fail(f"{where} must be a non-empty list")
    if not all(isinstance(item, str) and item for item in value):
        fail(f"{where} entries must be non-empty strings")
    return value


def relative_path(value, where):
    if not isinstance(value, str) or not value:
        fail(f"{where} must be a non-empty path")
    path = PurePath(value)
    windows_path = PureWindowsPath(value)
    if (
        path.is_absolute()
        or windows_path.is_absolute()
        or ".." in path.parts
        or ".." in windows_path.parts
        or value.startswith("~")
    ):
        fail(f"{where} must stay relative to HOME: {value!r}")
    return value


def agent_paths(value, where):
    for agent, paths in mapping(value, where).items():
        if agent not in agents:
            fail(f"{where}: unknown agent {agent!r}")
        root_parts = PurePath(
            relative_path(agents[agent], f"integration_agents.{agent}")
        ).parts
        for index, path in enumerate(string_list(paths, f"{where}.{agent}")):
            path = relative_path(path, f"{where}.{agent}[{index}]")
            if PurePath(path).parts[: len(root_parts)] != root_parts:
                fail(f"{where}.{agent}[{index}] must be below {agents[agent]!r}")


def command(value, where):
    items = string_list(value, where)
    if items.count("{args}") > 1:
        fail(f"{where} may contain {{args}} at most once")


for agent, path in agents.items():
    if agent not in tools:
        fail(f"agent root has unknown tool {agent!r}")
    relative_path(path, f"integration_agents.{agent}")

for owner, raw_spec in owners.items():
    if owner not in tools:
        fail(f"unknown owner {owner!r}")
    spec = mapping(raw_spec, owner)
    unknown = set(spec) - {"lifecycle", "targets"}
    if unknown:
        fail(f"{owner}: unknown fields {sorted(unknown)}")
    lifecycle = mapping(spec.get("lifecycle"), f"{owner}.lifecycle")
    unknown = set(lifecycle) - LIFECYCLE_KEYS
    if unknown:
        fail(f"{owner}.lifecycle: unknown fields {sorted(unknown)}")
    targets = spec.get("targets")
    if not isinstance(targets, list) or not targets:
        fail(f"{owner}.targets must be a non-empty list")
    target_names = set()
    for index, target in enumerate(targets):
        target = mapping(target, f"{owner}.targets[{index}]")
        if set(target) - {"args", "tool"}:
            fail(f"{owner}.targets[{index}] has unknown fields")
        agent = target.get("tool")
        if agent not in agents:
            fail(f"{owner}.targets[{index}]: unknown agent {agent!r}")
        if agent in target_names:
            fail(f"{owner}: duplicate target {agent!r}")
        target_names.add(agent)
        if "args" in target:
            string_list(target["args"], f"{owner}.targets[{index}].args", True)
    if "setup" in lifecycle and not isinstance(lifecycle["setup"], bool):
        fail(f"{owner}.lifecycle.setup must be boolean")
    if "os" in lifecycle:
        oses = set(string_list(lifecycle["os"], f"{owner}.lifecycle.os"))
        if oses - SUPPORTED_OS:
            fail(
                f"{owner}.lifecycle.os has unsupported values {sorted(oses - SUPPORTED_OS)}"
            )
    for field in ("binary", "label"):
        if field in lifecycle and (
            not isinstance(lifecycle[field], str) or not lifecycle[field]
        ):
            fail(f"{owner}.lifecycle.{field} must be a non-empty string")
    for field in ("setup", "uninstall_disabled"):
        if field in lifecycle and not isinstance(lifecycle[field], bool):
            fail(f"{owner}.lifecycle.{field} must be boolean")
    if lifecycle.get("setup", True) and not lifecycle.get("binary"):
        fail(f"{owner}.lifecycle.binary is required when setup is enabled")
    if lifecycle.get("uninstall_disabled") and "uninstall" not in lifecycle:
        fail(f"{owner}.lifecycle.uninstall_disabled requires uninstall")
    if lifecycle.get("uninstall_all") and "uninstall" not in lifecycle:
        fail(f"{owner}.lifecycle.uninstall_all requires uninstall")
    timeout = lifecycle.get("timeout_seconds", 30)
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
        fail(f"{owner}.lifecycle.timeout_seconds must be a positive integer")
    for field in ("install", "uninstall"):
        if field in lifecycle:
            command(lifecycle[field], f"{owner}.lifecycle.{field}")
    for field in ("skip_errors", "uninstall_all"):
        if field in lifecycle:
            string_list(lifecycle[field], f"{owner}.lifecycle.{field}", True)

    cleanup = mapping(lifecycle.get("cleanup", {}), f"{owner}.cleanup")
    unknown = set(cleanup) - CLEANUP_KEYS
    if unknown:
        fail(f"{owner}.cleanup: unknown fields {sorted(unknown)}")
    for field in ("command_exact", "command_fields", "command_prefixes", "needles"):
        if field in cleanup:
            string_list(cleanup[field], f"{owner}.cleanup.{field}", True)
    for field in ("standalone", "json_hooks"):
        if field in cleanup:
            agent_paths(cleanup[field], f"{owner}.cleanup.{field}")
    if cleanup.get("json_hooks") and not any(
        cleanup.get(field) for field in ("command_exact", "command_prefixes", "needles")
    ):
        fail(f"{owner}.cleanup.json_hooks requires a command matcher")
    for index, path in enumerate(cleanup.get("extras", [])):
        relative_path(path, f"{owner}.cleanup.extras[{index}]")

    markdown = mapping(
        cleanup.get("markdown_refs", {}), f"{owner}.cleanup.markdown_refs"
    )
    if set(markdown) - {"agents", "patterns"}:
        fail(f"{owner}.cleanup.markdown_refs has unknown fields")
    if markdown:
        agent_paths(markdown.get("agents", {}), f"{owner}.cleanup.markdown_refs.agents")
        for pattern in string_list(
            markdown.get("patterns"), f"{owner}.cleanup.markdown_refs.patterns"
        ):
            try:
                re.compile(pattern)
            except re.error as err:
                fail(f"{owner}: invalid markdown regex {pattern!r}: {err}")

    for index, rule in enumerate(cleanup.get("managed_blocks", [])):
        rule = mapping(rule, f"{owner}.cleanup.managed_blocks[{index}]")
        if set(rule) != {"end", "path", "start"}:
            fail(f"{owner}.cleanup.managed_blocks[{index}] requires path/start/end")
        relative_path(rule["path"], f"{owner}.cleanup.managed_blocks[{index}].path")
        if not all(
            isinstance(rule[key], str) and rule[key] for key in ("start", "end")
        ):
            fail(f"{owner}.cleanup.managed_blocks[{index}] markers must be non-empty")

    marked = mapping(cleanup.get("marked_files", {}), f"{owner}.cleanup.marked_files")
    for agent, rules in marked.items():
        if agent not in agents:
            fail(f"{owner}.cleanup.marked_files: unknown agent {agent!r}")
        if not isinstance(rules, list):
            fail(f"{owner}.cleanup.marked_files.{agent} must be a list")
        for index, rule in enumerate(rules):
            rule = mapping(rule, f"{owner}.cleanup.marked_files.{agent}[{index}]")
            if set(rule) - {"contains", "head_chars", "head_contains", "path"}:
                fail(
                    f"{owner}.cleanup.marked_files.{agent}[{index}] has unknown fields"
                )
            path = relative_path(
                rule.get("path"), f"{owner}.cleanup.marked_files.{agent}[{index}].path"
            )
            root_parts = PurePath(agents[agent]).parts
            if PurePath(path).parts[: len(root_parts)] != root_parts:
                fail(
                    f"{owner}.cleanup.marked_files.{agent}[{index}].path must be below {agents[agent]!r}"
                )
            for field in ("contains", "head_contains"):
                if field in rule:
                    string_list(
                        rule[field],
                        f"{owner}.cleanup.marked_files.{agent}[{index}].{field}",
                        True,
                    )
            if "head_chars" in rule and (
                not isinstance(rule["head_chars"], int) or rule["head_chars"] < 0
            ):
                fail(
                    f"{owner}.cleanup.marked_files.{agent}[{index}].head_chars must be non-negative"
                )

    envs = mapping(lifecycle.get("target_env", {}), f"{owner}.target_env")
    if set(envs) - target_names:
        fail(
            f"{owner}.target_env has non-target agents {sorted(set(envs) - target_names)}"
        )
    for agent, values in envs.items():
        for key, value in mapping(values, f"{owner}.target_env.{agent}").items():
            if not isinstance(key, str) or (
                value is not None and not isinstance(value, str)
            ):
                fail(f"{owner}.target_env.{agent} values must be string or null")

    posts = mapping(lifecycle.get("post_install", {}), f"{owner}.post_install")
    if set(posts) - target_names:
        fail(
            f"{owner}.post_install has non-target agents {sorted(set(posts) - target_names)}"
        )
    for agent, rule in posts.items():
        rule = mapping(rule, f"{owner}.post_install.{agent}")
        if set(rule) - {"move", "replacements"}:
            fail(f"{owner}.post_install.{agent} has unknown fields")
        move = mapping(rule.get("move"), f"{owner}.post_install.{agent}.move")
        if set(move) != {"from", "to"}:
            fail(f"{owner}.post_install.{agent}.move requires from/to")
        from_path = relative_path(
            move["from"], f"{owner}.post_install.{agent}.move.from"
        )
        to_path = relative_path(move["to"], f"{owner}.post_install.{agent}.move.to")
        root_parts = PurePath(agents[agent]).parts
        for field, path in (("from", from_path), ("to", to_path)):
            if PurePath(path).parts[: len(root_parts)] != root_parts:
                fail(
                    f"{owner}.post_install.{agent}.move.{field} must be below {agents[agent]!r}"
                )
        for index, pair in enumerate(rule.get("replacements", [])):
            if (
                not isinstance(pair, list)
                or len(pair) != 2
                or not all(isinstance(v, str) for v in pair)
            ):
                fail(
                    f"{owner}.post_install.{agent}.replacements[{index}] must be two strings"
                )

print("ok integration schema")
