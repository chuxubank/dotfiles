NEEDLES = [
    ".orca/agent-hooks/",
    "ORCA_AGENT_HOOK_",
    "@orca-managed",
]

STANDALONE = {
    "github-copilot": [".copilot/hooks/orca.json"],
    "grok": [".grok/hooks/orca-status.json"],
    "pi": [
        ".pi/agent/extensions/orca-agent-status.ts",
        ".pi/agent/extensions/orca-prefill.ts",
        ".pi/agent/extensions/orca-titlebar-spinner.ts",
    ],
}

JSON_HOOKS = {
    "claude-code": [".claude/settings.json", ".claude/hooks.json"],
    "codex": [".codex/hooks.json", ".codex/hooks.json.bak"],
    "cursor": [".cursor/hooks.json", ".cursor/hooks.json.bak"],
}

EMPTY_DIR_STOP = {
    "claude-code": ".claude",
    "codex": ".codex",
    "cursor": ".cursor",
    "gemini-cli": ".gemini",
    "github-copilot": ".copilot",
    "grok": ".grok",
    "opencode": ".config/opencode",
    "pi": ".pi",
}

KIMI_START = "# >>> orca-managed-kimi-hooks"
KIMI_END = "# <<< orca-managed-kimi-hooks <<<"


def is_orca_hook_entry(entry):
    if not isinstance(entry, dict):
        return False
    if entry_matches(entry, NEEDLES):
        return True
    return text_has_needles(entry.get("bash"), NEEDLES)


def strip_managed_block(path, start, end):
    if not path.is_file():
        return
    original = path.read_text()
    first = original.find(start)
    if first < 0:
        return
    last = original.find(end, first)
    if last < 0:
        print("Orca cleanup: skip unterminated block in %s" % path, file=sys.stderr)
        return
    last += len(end)
    if last < len(original) and original[last] == "\n":
        last += 1
    text = original[:first] + original[last:]
    if text.strip():
        path.write_text(text)
        print("  stripped Orca block from %s" % path)
    else:
        path.unlink()
        print("  removed %s" % path)


def clean_agent(name):
    stop = HOME / EMPTY_DIR_STOP.get(name, "")
    for rel in STANDALONE.get(name, []):
        path = HOME / rel
        if remove_path(path):
            rmdir_empty(path.parent, stop)
    for rel in JSON_HOOKS.get(name, []):
        clean_json_hooks(HOME / rel, is_orca_hook_entry)


def remove_agents(agents, extras=False):
    unknown = [name for name in agents if name not in EMPTY_DIR_STOP]
    if unknown:
        print("Orca cleanup: unknown agent(s): %s" % ", ".join(unknown), file=sys.stderr)
        sys.exit(1)
    for name in agents:
        clean_agent(name)
    if extras:
        strip_managed_block(HOME / ".kimi-code/config.toml", KIMI_START, KIMI_END)
