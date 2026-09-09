import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

HOME = Path.home()


def home_path(relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or str(relative).startswith("~"):
        raise ValueError("integration path must stay relative to HOME: %r" % relative)
    root = HOME.resolve()
    candidate = HOME / path
    resolved = candidate.resolve(strict=False)
    if resolved != root and root not in resolved.parents:
        raise ValueError(
            "integration path escapes HOME through a symlink: %r" % relative
        )
    return candidate


def atomic_write_text(path, text):
    if path.is_symlink():
        path = path.resolve(strict=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else None
    fd, temporary = tempfile.mkstemp(prefix=".%s." % path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        if mode is not None:
            os.chmod(temporary, mode)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def text_matches(text, cleanup):
    if not isinstance(text, str):
        return False
    value = text.strip()
    if value in cleanup.get("command_exact", []):
        return True
    if any(value.startswith(prefix) for prefix in cleanup.get("command_prefixes", [])):
        return True
    return any(needle in text for needle in cleanup.get("needles", []))


def entry_matches(entry, cleanup):
    if not isinstance(entry, dict):
        return False
    fields = cleanup.get("command_fields") or ["command"]
    if any(text_matches(entry.get(field), cleanup) for field in fields):
        return True
    nested = entry.get("hooks")
    return (
        isinstance(nested, list)
        and nested
        and all(entry_matches(item, cleanup) for item in nested)
    )


def scrub_hooks(node, cleanup):
    if isinstance(node, list):
        kept = []
        for entry in node:
            if entry_matches(entry, cleanup):
                continue
            if isinstance(entry, dict) and isinstance(entry.get("hooks"), list):
                inner = scrub_hooks(entry["hooks"], cleanup)
                if not inner:
                    continue
                entry = dict(entry)
                entry["hooks"] = inner
            kept.append(entry)
        return kept
    if not isinstance(node, dict):
        return node
    out = {}
    for key, value in node.items():
        cleaned = scrub_hooks(value, cleanup)
        if cleaned not in ([], {}):
            out[key] = cleaned
    return out


def remove_path(path):
    if path.is_file() or path.is_symlink():
        path.unlink()
        print("  removed %s" % path)
        return True
    return False


def rmdir_empty(path, stop):
    if not stop:
        return
    stop = stop.resolve()
    current = path.resolve()
    while current != stop and stop in current.parents:
        try:
            current.rmdir()
        except OSError:
            return
        print("  removed %s" % current)
        current = current.parent


def clean_json_hooks(path, cleanup):
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as err:
        print("integration cleanup: skip %s (%s)" % (path, err), file=sys.stderr)
        return
    if not isinstance(data, dict) or "hooks" not in data:
        return
    cleaned = scrub_hooks(data.get("hooks"), cleanup)
    if cleaned == data.get("hooks"):
        return
    if cleaned in ([], {}):
        data.pop("hooks", None)
    else:
        data["hooks"] = cleaned
    if list(data.keys()) == ["version"] or data == {}:
        path.unlink()
        print("  removed %s" % path)
        return
    atomic_write_text(path, json.dumps(data, indent=2) + "\n")
    print("  stripped hooks from %s" % path)


def strip_matching_lines(path, patterns):
    if not path.is_file():
        return
    regexes = [re.compile(pattern) for pattern in patterns]
    original = path.read_text()
    lines = original.splitlines(True)
    kept = [line for line in lines if not any(rx.match(line.strip()) for rx in regexes)]
    if kept == lines:
        return
    text = "".join(kept)
    if text.strip():
        atomic_write_text(path, text)
        print("  stripped managed references from %s" % path)
    else:
        path.unlink()
        print("  removed %s" % path)


def strip_managed_block(path, start, end):
    if not path.is_file():
        return
    original = path.read_text()
    first = original.find(start)
    if first < 0:
        return
    last = original.find(end, first)
    if last < 0:
        print(
            "integration cleanup: skip unterminated block in %s" % path, file=sys.stderr
        )
        return
    last += len(end)
    if last < len(original) and original[last] == "\n":
        last += 1
    text = original[:first] + original[last:]
    if text.strip():
        atomic_write_text(path, text)
        print("  stripped managed block from %s" % path)
    else:
        path.unlink()
        print("  removed %s" % path)


def remove_marked_file(path, rule):
    if not path.is_file():
        return
    text = path.read_text()
    contains = any(marker in text for marker in rule.get("contains", []))
    head = text[: rule.get("head_chars", 0)]
    head_contains = any(marker in head for marker in rule.get("head_contains", []))
    if contains or head_contains:
        path.unlink()
        print("  removed %s" % path)


def clean_targets(cleanup, names, agent_roots, extras=False):
    known = set(agent_roots)
    unknown = [name for name in names if name not in known]
    if unknown:
        raise SystemExit(
            "integration cleanup: unknown agent(s): %s" % ", ".join(unknown)
        )
    for name in names:
        stop = home_path(agent_roots[name])
        for rel in cleanup.get("standalone", {}).get(name, []):
            path = home_path(rel)
            if remove_path(path):
                rmdir_empty(path.parent, stop)
        for rel in cleanup.get("json_hooks", {}).get(name, []):
            clean_json_hooks(home_path(rel), cleanup)
        markdown = cleanup.get("markdown_refs", {})
        for rel in markdown.get("agents", {}).get(name, []):
            strip_matching_lines(home_path(rel), markdown.get("patterns", []))
        for rule in cleanup.get("marked_files", {}).get(name, []):
            remove_marked_file(home_path(rule["path"]), rule)
    if extras:
        for rel in cleanup.get("extras", []):
            path = home_path(rel)
            if remove_path(path):
                rmdir_empty(path.parent, path.parent.parent)
        for rule in cleanup.get("managed_blocks", []):
            strip_managed_block(home_path(rule["path"]), rule["start"], rule["end"])


def expand_command(template, item):
    command = []
    for value in template:
        if value == "{args}":
            command.extend(item.get("args") or [])
        else:
            command.append(os.path.expanduser(str(value)))
    return command


def command_env(lifecycle, item):
    env = os.environ.copy()
    for key, value in lifecycle.get("target_env", {}).get(item["tool"], {}).items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = os.path.expanduser(str(value))
    return env


def run_command(lifecycle, action, item):
    template = lifecycle.get(action)
    if not template:
        return None
    try:
        proc = subprocess.run(
            expand_command(template, item),
            capture_output=True,
            text=True,
            env=command_env(lifecycle, item),
            timeout=lifecycle.get("timeout_seconds", 30),
        )
    except subprocess.TimeoutExpired:
        print(
            "integration %s timed out after %ss"
            % (item["tool"], lifecycle.get("timeout_seconds", 30)),
            file=sys.stderr,
        )
        return 124
    if proc.stdout:
        sys.stdout.write(proc.stdout)
        if not proc.stdout.endswith("\n"):
            sys.stdout.write("\n")
    if proc.returncode not in (0, None):
        error = (proc.stderr or "") + (proc.stdout or "")
        if any(
            needle.lower() in error.lower()
            for needle in lifecycle.get("skip_errors", [])
        ):
            detail = error.strip().splitlines()[-1] if error.strip() else "not found"
            print("  skip %s: %s" % (item["tool"], detail))
            return 0
    if proc.stderr:
        sys.stderr.write(proc.stderr)
        if not proc.stderr.endswith("\n"):
            sys.stderr.write("\n")
    return proc.returncode


def post_install(lifecycle, item, agent_roots):
    rule = lifecycle.get("post_install", {}).get(item["tool"])
    if not rule:
        return
    move = rule.get("move")
    if not move:
        return
    src = home_path(move["from"])
    dst = home_path(move["to"])
    if not src.is_file():
        print("  skip %s: hook not installed" % item["tool"])
        return
    text = src.read_text()
    for old, new in rule.get("replacements", []):
        text = text.replace(old, new)
    if not dst.is_file() or dst.read_text() != text:
        atomic_write_text(dst, text)
        print("  wrote %s" % dst)
    src.unlink()
    print("  removed %s" % src)
    rmdir_empty(src.parent, home_path(agent_roots[item["tool"]]))


def reconcile(spec, mode, agent_roots):
    owner = spec["owner"]
    lifecycle = spec["lifecycle"]
    targets = spec["targets"]
    cleanup = lifecycle.get("cleanup", {})
    label = lifecycle.get("label") or owner
    binary = lifecycle.get("binary")
    installed = not binary or shutil.which(binary)
    names = [item["tool"] for item in targets]

    if mode == "teardown":
        print("󰯁 Teardown %s agent integrations" % label)
        errors = []
        if installed and lifecycle.get("uninstall"):
            for item in targets:
                code = run_command(lifecycle, "uninstall", item)
                if code not in (0, None):
                    errors.append((item["tool"], code))
            declared = {arg for item in targets for arg in item.get("args", [])}
            for target in lifecycle.get("uninstall_all", []):
                if target not in declared:
                    code = run_command(
                        lifecycle, "uninstall", {"tool": target, "args": [target]}
                    )
                    if code not in (0, None):
                        errors.append((target, code))
        clean_targets(cleanup, names, agent_roots, extras=True)
        if errors:
            print(
                "%s uninstall failed: %s"
                % (
                    label,
                    ", ".join("%s=%s" % error for error in errors),
                ),
                file=sys.stderr,
            )
            raise SystemExit(1)
        return

    print("󰯁 Setup %s agent integrations" % label)
    if not installed:
        print("%s is not installed; removing leftover agent integrations" % label)
        clean_targets(cleanup, names, agent_roots, extras=True)
        return
    for item in targets:
        if item["enabled"]:
            print("  init %s" % item["tool"])
            code = run_command(lifecycle, "install", item)
            if code not in (0, None):
                raise SystemExit(code)
            post_install(lifecycle, item, agent_roots)
    disabled = [item for item in targets if not item["enabled"]]
    uninstall_errors = []
    if lifecycle.get("uninstall_disabled") and lifecycle.get("uninstall"):
        for item in disabled:
            code = run_command(lifecycle, "uninstall", item)
            if code not in (0, None):
                uninstall_errors.append((item["tool"], code))
    for item in disabled:
        print("  remove %s" % item["tool"])
    if disabled:
        clean_targets(cleanup, [item["tool"] for item in disabled], agent_roots)
    if uninstall_errors:
        print(
            "%s uninstall failed: %s"
            % (
                label,
                ", ".join("%s=%s" % error for error in uninstall_errors),
            ),
            file=sys.stderr,
        )
        raise SystemExit(1)
