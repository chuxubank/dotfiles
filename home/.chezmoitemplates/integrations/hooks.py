import json
import re
import sys
from pathlib import Path

HOME = Path.home()
RTK_REF = re.compile(r"^@(?:.*/)?RTK\.md\s*$")


def text_has_needles(text, needles):
    if not isinstance(text, str):
        return False
    return any(needle in text for needle in needles)


def entry_matches(entry, needles):
    if not isinstance(entry, dict):
        return False
    if text_has_needles(entry.get("command"), needles):
        return True
    nested = entry.get("hooks")
    if isinstance(nested, list) and nested and all(
        entry_matches(item, needles) for item in nested
    ):
        return True
    return False


def scrub_hook_list(entries, match):
    kept = []
    for entry in entries:
        if match(entry):
            continue
        if isinstance(entry, dict) and isinstance(entry.get("hooks"), list):
            inner = scrub_hook_list(entry["hooks"], match)
            if not inner:
                continue
            entry = dict(entry)
            entry["hooks"] = inner
        kept.append(entry)
    return kept


def scrub_hooks_node(node, match):
    if isinstance(node, list):
        return scrub_hook_list(node, match)
    if not isinstance(node, dict):
        return node
    out = {}
    for key, value in node.items():
        cleaned = scrub_hooks_node(value, match)
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


def clean_json_hooks(path, match):
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as err:
        print("hook cleanup: skip %s (%s)" % (path, err), file=sys.stderr)
        return
    if not isinstance(data, dict) or "hooks" not in data:
        return
    cleaned = scrub_hooks_node(data.get("hooks"), match)
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
    print("  stripped hooks from %s" % path)
