import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HOME = Path.home()


class InventoryError(RuntimeError):
    pass


def home_path(relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or str(relative).startswith("~"):
        raise ValueError("plugin path must stay relative to HOME: %r" % relative)
    root = HOME.resolve()
    candidate = HOME / path
    resolved = candidate.resolve(strict=False)
    if resolved != root and root not in resolved.parents:
        raise ValueError("plugin path escapes HOME through a symlink: %r" % relative)
    return candidate


def value_at(value, path, default=None):
    current = value
    for part in path:
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def load_json(inventory):
    if "file" in inventory:
        path = home_path(inventory["file"])
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text())
        except (OSError, UnicodeDecodeError, ValueError) as err:
            raise InventoryError("Could not read %s: %s" % (inventory["label"], err))
    try:
        proc = subprocess.run(
            inventory["command"], capture_output=True, text=True, timeout=30
        )
    except (OSError, subprocess.TimeoutExpired) as err:
        raise InventoryError("Could not list %s: %s" % (inventory["label"], err))
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        raise InventoryError(
            "Could not list %s%s"
            % (inventory["label"], ": " + detail if detail else "")
        )
    try:
        return json.loads(proc.stdout)
    except ValueError as err:
        raise InventoryError("Could not parse %s: %s" % (inventory["label"], err))


def load_inventory(inventory):
    data = load_json(inventory)
    if data is None:
        return []
    collection = value_at(data, inventory["path"])
    mode = inventory["mode"]
    prefix = inventory.get("prefix", "")
    entries = []
    if mode == "keys":
        if not isinstance(collection, dict):
            raise InventoryError("%s listing is not an object" % inventory["label"])
        raw_entries = list(collection)
    else:
        if not isinstance(collection, list):
            raise InventoryError("%s listing is not an array" % inventory["label"])
        raw_entries = collection
    for item in raw_entries:
        if mode == "keys":
            name = item
        elif mode == "string_or_field" and isinstance(item, str):
            name = item
        elif isinstance(item, dict):
            name = value_at(item, inventory["field"])
        else:
            name = None
        if not isinstance(name, str) or not name:
            raise InventoryError("%s contains an invalid name" % inventory["label"])
        entry = {"name": prefix + name, "enabled": True, "sources": []}
        if isinstance(item, dict) and inventory.get("enabled_field"):
            enabled = value_at(item, inventory["enabled_field"], True)
            entry["enabled"] = enabled is not False
        if isinstance(item, dict):
            for field in inventory.get("source_fields", []):
                source = value_at(item, field)
                if isinstance(source, str) and source:
                    entry["sources"].append(source)
        entries.append(entry)
    return entries


def command_args(template, values):
    command = []
    for token in template:
        if token == "{ref_args}":
            if values.get("ref"):
                command.extend(["--ref", values["ref"]])
            continue
        value = values.get(token[1:-1]) if token.startswith("{") and token.endswith("}") else token
        if value is None:
            raise ValueError("unknown plugin command placeholder: %s" % token)
        command.append(str(value))
    return command


def run_command(template, values, quiet=False):
    command = command_args(template, values)
    if quiet:
        return subprocess.run(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300
        ).returncode
    return subprocess.run(command, timeout=300).returncode


def preserved_marketplaces(rules):
    names = set()
    for rule in rules:
        path = home_path(rule["file"])
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text())
        except (OSError, UnicodeDecodeError, ValueError) as err:
            raise InventoryError("Could not read marketplace protection %s: %s" % (path, err))
        value = value_at(data, rule["path"])
        if not isinstance(value, dict):
            raise InventoryError(
                "Marketplace protection %s has an invalid path %r"
                % (path, rule["path"])
            )
        names.update(value)
    return names


def normalize_identity(manager, value, strict=False):
    if manager.get("identity_transform") == "npm_name":
        if not value.startswith("npm:"):
            if strict:
                raise ValueError("npm identity must start with npm: %r" % value)
            return value
        spec = value[4:]
        version_at = spec.find("@", 1 if spec.startswith("@") else 0)
        if version_at >= 0:
            spec = spec[:version_at]
        if not spec:
            raise ValueError("npm identity has an empty package name: %r" % value)
        return "npm:" + spec
    return value


def resource_identity(manager, item):
    return normalize_identity(manager, item[manager["identity"]], strict=True)


def desired_resources(manager):
    return {
        resource_identity(manager, item): item
        for item in manager["declared_plugins"]
        if item.get("enabled", False)
    }


def cleanup_resources(manager, inventory, uninstall):
    installed = load_inventory(inventory)
    desired_ids = desired_resources(manager)
    had_errors = False
    for item in installed:
        if normalize_identity(manager, item["name"]) not in desired_ids:
            print("Remove undeclared %s plugin: %s" % (manager["label"], item["name"]))
            if run_command(uninstall, {"installed": item["name"]}) != 0:
                had_errors = True
    return had_errors


def reconcile_resources(manager, cleanup=True):
    installed = load_inventory(manager["inventory"])
    installed_by_name = {
        normalize_identity(manager, item["name"]): item for item in installed
    }
    desired_ids = desired_resources(manager)
    had_errors = False

    for key, item in desired_ids.items():
        current = installed_by_name.get(key)
        if current is None:
            print("Install %s plugin: %s" % (manager["label"], key))
            if run_command(manager["install"], item) != 0:
                print("Could not install %s plugin %s" % (manager["label"], key), file=sys.stderr)
                had_errors = True
                continue
            current = {"name": key, "enabled": True}
        if manager.get("enable") and not current.get("enabled", True):
            print("Enable %s plugin: %s" % (manager["label"], key))
            if run_command(manager["enable"], item) != 0:
                print("Could not enable %s plugin %s" % (manager["label"], key), file=sys.stderr)
                had_errors = True

    if cleanup and not had_errors:
        for item in installed:
            if normalize_identity(manager, item["name"]) not in desired_ids:
                print("Remove undeclared %s plugin: %s" % (manager["label"], item["name"]))
                if run_command(manager["uninstall"], {"installed": item["name"]}) != 0:
                    had_errors = True
    return had_errors


def reconcile_marketplaces(manager):
    config = manager.get("marketplaces")
    if not config:
        return False
    installed = load_inventory(config["inventory"])
    desired = [item for item in manager.get("declared_marketplaces", []) if item["enabled"]]
    preserved = preserved_marketplaces(config.get("preserve", []))
    had_errors = False

    for item in desired:
        present = any(
            entry["name"] == item["name"] or item["source"] in entry["sources"]
            for entry in installed
        )
        if not present:
            print("Add %s marketplace: %s" % (manager["label"], item["name"]))
            if run_command(config["install"], item) != 0:
                had_errors = True

    if not had_errors:
        desired_names = {item["name"] for item in desired}
        desired_sources = {item["source"] for item in desired}
        for entry in installed:
            declared = entry["name"] in desired_names or bool(
                set(entry["sources"]) & desired_sources
            )
            if declared or entry["name"] in preserved:
                continue
            print("Remove undeclared %s marketplace: %s" % (manager["label"], entry["name"]))
            if run_command(config["uninstall"], {"installed": entry["name"]}) != 0:
                had_errors = True
    return had_errors


def reconcile(manager):
    for path in reversed(manager.get("path_prepend", [])):
        os.environ["PATH"] = os.path.expanduser(path) + os.pathsep + os.environ["PATH"]
    if not shutil.which(manager["binary"]):
        return
    try:
        market_errors = reconcile_marketplaces(manager)
        cleanup_before = manager.get("cleanup_order") == "before"
        cleanup_errors = cleanup_before and cleanup_resources(
            manager, manager["cleanup_inventory"], manager["uninstall"]
        )
        plugin_errors = False
        if manager.get("install"):
            plugin_errors = reconcile_resources(manager, cleanup=not cleanup_before)
    except InventoryError as err:
        print(str(err), file=sys.stderr)
        raise SystemExit(1)
    if market_errors or cleanup_errors or plugin_errors:
        raise SystemExit(1)
