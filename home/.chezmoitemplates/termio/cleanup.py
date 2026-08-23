NEEDLES = ["termio-hooks", "termio agent report", "Application Support/termio"]

STANDALONE = {
    "grok": [".grok/hooks/termio.json"],
    "opencode": [".config/opencode/plugin/termio.js"],
    "pi": [".pi/agent/extensions/termio.js"],
}

JSON_HOOKS = {
    "claude-code": [".claude/settings.json"],
    "codex": [".codex/hooks.json"],
    "cursor": [".cursor/hooks.json"],
}

EMPTY_DIR_STOP = {
    "claude-code": ".claude",
    "codex": ".codex",
    "cursor": ".cursor",
    "grok": ".grok",
    "opencode": ".config/opencode",
    "pi": ".pi",
}

EXTRA_STANDALONE = [
    ".config/amp/plugins/termio.ts",
]


def is_termio_hook_entry(entry):
    return entry_matches(entry, NEEDLES)


def clean_agent(name):
    stop = HOME / EMPTY_DIR_STOP.get(name, "")
    for rel in STANDALONE.get(name, []):
        path = HOME / rel
        if remove_path(path):
            rmdir_empty(path.parent, stop)
    for rel in JSON_HOOKS.get(name, []):
        clean_json_hooks(HOME / rel, is_termio_hook_entry)


def remove_agents(agents, extras=False):
    unknown = [name for name in agents if name not in EMPTY_DIR_STOP]
    if unknown:
        print("termio cleanup: unknown agent(s): %s" % ", ".join(unknown), file=sys.stderr)
        sys.exit(1)
    for name in agents:
        clean_agent(name)
    if extras:
        for rel in EXTRA_STANDALONE:
            path = HOME / rel
            if remove_path(path):
                rmdir_empty(path.parent, path.parent.parent)
