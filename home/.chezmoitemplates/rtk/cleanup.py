import json
import re
import sys
from pathlib import Path

HOME = Path.home()
RTK_REF = re.compile(r"^@(?:.*/)?RTK\.md\s*$")

STANDALONE = {
    "claude-code": [".claude/RTK.md"],
    "codex": [".codex/RTK.md"],
    "gemini-cli": [
        ".gemini/hooks/rtk-hook-gemini.sh",
        ".gemini/hooks/.rtk-hook.sha256",
    ],
    "opencode": [".config/opencode/plugins/rtk.ts"],
    "pi": [".pi/agent/extensions/rtk.ts"],
}

MD_REFS = {
    "claude-code": [".claude/CLAUDE.md"],
    "codex": [".codex/AGENTS.md"],
}

INSTRUCTION_FILES = {
    "gemini-cli": [".gemini/GEMINI.md"],
}

JSON_HOOKS = {
    "claude-code": [".claude/settings.json"],
    "gemini-cli": [".gemini/settings.json"],
    "cursor": [".cursor/hooks.json"],
}

EMPTY_DIR_STOP = {
    "claude-code": ".claude",
    "codex": ".codex",
    "gemini-cli": ".gemini",
    "opencode": ".config/opencode",
    "pi": ".pi",
    "cursor": ".cursor",
}


def is_rtk_command(cmd):
    if not isinstance(cmd, str):
        return False
    text = cmd.strip()
    if not text:
        return False
    if "rtk hook" in text or "rtk-hook-" in text:
        return True
    return text == "rtk" or text.startswith("rtk ")


def is_rtk_hook_entry(entry):
    if not isinstance(entry, dict):
        return False
    if is_rtk_command(entry.get("command")):
        return True
    nested = entry.get("hooks")
    if isinstance(nested, list) and nested and all(is_rtk_hook_entry(item) for item in nested):
        return True
    return False


def scrub_hook_list(entries):
    kept = []
    for entry in entries:
        if is_rtk_hook_entry(entry):
            continue
        if isinstance(entry, dict) and isinstance(entry.get("hooks"), list):
            inner = scrub_hook_list(entry["hooks"])
            if not inner:
                continue
            entry = dict(entry)
            entry["hooks"] = inner
        kept.append(entry)
    return kept


def scrub_hooks_node(node):
    if isinstance(node, list):
        return scrub_hook_list(node)
    if not isinstance(node, dict):
        return node
    out = {}
    for key, value in node.items():
        cleaned = scrub_hooks_node(value)
        if cleaned in ([], {}):
            continue
        out[key] = cleaned
    return out


def remove_path(path):
    if path.is_file() or path.is_symlink():
        path.unlink()
        print("  removed %s" % path)
        return True
    return False


def rmdir_empty(path, stop):
    stop = stop.resolve()
    current = path.resolve()
    while current != stop and stop in current.parents:
        try:
            current.rmdir()
        except OSError:
            return
        print("  removed %s" % current)
        current = current.parent


def strip_md_refs(path):
    if not path.is_file():
        return
    original = path.read_text()
    lines = original.splitlines(True)
    kept = [line for line in lines if not RTK_REF.match(line.strip())]
    if kept == lines:
        return
    text = "".join(kept)
    if not text.strip():
        path.unlink()
        print("  removed %s" % path)
        return
    path.write_text(text)
    print("  stripped RTK.md ref in %s" % path)


def remove_instruction_file(path):
    if not path.is_file():
        return
    text = path.read_text()
    head = text[:120]
    if "Rust Token Killer" in text or "# RTK" in head:
        path.unlink()
        print("  removed %s" % path)


def clean_json_hooks(path):
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as err:
        print("rtk cleanup: skip %s (%s)" % (path, err), file=sys.stderr)
        return
    if not isinstance(data, dict) or "hooks" not in data:
        return
    cleaned = scrub_hooks_node(data.get("hooks"))
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
    path.write_text(json.dumps(data, indent=2) + "\n")
    print("  stripped rtk hooks from %s" % path)


def clean_agent(name):
    stop = HOME / EMPTY_DIR_STOP.get(name, "")
    for rel in STANDALONE.get(name, []):
        path = HOME / rel
        if remove_path(path):
            rmdir_empty(path.parent, stop)
    for rel in MD_REFS.get(name, []):
        strip_md_refs(HOME / rel)
    for rel in INSTRUCTION_FILES.get(name, []):
        remove_instruction_file(HOME / rel)
    for rel in JSON_HOOKS.get(name, []):
        clean_json_hooks(HOME / rel)


def remove_agents(agents):
    unknown = [name for name in agents if name not in EMPTY_DIR_STOP]
    if unknown:
        print("rtk cleanup: unknown agent(s): %s" % ", ".join(unknown), file=sys.stderr)
        sys.exit(1)
    for name in agents:
        clean_agent(name)
