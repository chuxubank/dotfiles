NEEDLES = ["herdr-agent-state.sh", "herdr-agent-state.ts", "herdr-agent-state.js"]

STANDALONE = {
    "claude-code": [".claude/hooks/herdr-agent-state.sh"],
    "codex": [".codex/herdr-agent-state.sh"],
    "cursor": [".cursor/herdr-agent-state.sh"],
    "gemini-cli": [".gemini/config/hooks/herdr-agent-state.sh"],
    "github-copilot": [".copilot/hooks/herdr-agent-state.sh"],
    "grok": [
        ".grok/hooks/herdr-agent-state.sh",
        ".grok/hooks/herdr.json",
    ],
    "opencode": [".config/opencode/plugins/herdr-agent-state.js"],
    "pi": [".pi/agent/extensions/herdr-agent-state.ts"],
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
    "gemini-cli": ".gemini",
    "github-copilot": ".copilot",
    "grok": ".grok",
    "opencode": ".config/opencode",
    "pi": ".pi",
}

EXTRA_STANDALONE = [
    ".omp/agent/extensions/herdr-omp-agent-state.ts",
    ".config/devin/herdr-agent-state.sh",
    ".factory/hooks/herdr-agent-state.sh",
    ".kimi-code/hooks/herdr-agent-state.sh",
    ".config/kilo/plugin/herdr-agent-state.js",
    ".hermes/plugins/herdr-agent-state/__init__.py",
    ".qoder/hooks/herdr-agent-state.sh",
    ".mastracode/hooks/herdr-agent-state.sh",
]


def is_herdr_hook_entry(entry):
    return entry_matches(entry, NEEDLES)


def clean_agent(name):
    stop = HOME / EMPTY_DIR_STOP.get(name, "")
    for rel in STANDALONE.get(name, []):
        path = HOME / rel
        if remove_path(path):
            rmdir_empty(path.parent, stop)
    for rel in JSON_HOOKS.get(name, []):
        clean_json_hooks(HOME / rel, is_herdr_hook_entry)


def remove_agents(agents, extras=False):
    unknown = [name for name in agents if name not in EMPTY_DIR_STOP]
    if unknown:
        print("herdr cleanup: unknown agent(s): %s" % ", ".join(unknown), file=sys.stderr)
        sys.exit(1)
    for name in agents:
        clean_agent(name)
    if extras:
        for rel in EXTRA_STANDALONE:
            path = HOME / rel
            if remove_path(path):
                rmdir_empty(path.parent, path.parent.parent)
