STANDALONE = {
    "claude-code": [".claude/RTK.md"],
    "codex": [".codex/RTK.md"],
    "gemini-cli": [
        ".gemini/hooks/rtk-hook-gemini.sh",
        ".gemini/hooks/.rtk-hook.sha256",
    ],
    "opencode": [".config/opencode/plugins/rtk.ts"],
    "pi": [".pi/agent/extensions/rtk.ts"],
    "github-copilot": [".copilot/hooks/rtk-rewrite.json"],
}

MD_REFS = {
    "claude-code": [".claude/CLAUDE.md"],
    "codex": [".codex/AGENTS.md"],
}

INSTRUCTION_FILES = {
    "gemini-cli": [".gemini/GEMINI.md"],
    "github-copilot": [".copilot/copilot-instructions.md"],
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
    "github-copilot": ".copilot",
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
        clean_json_hooks(HOME / rel, is_rtk_hook_entry)


def remove_agents(agents, extras=False):
    unknown = [name for name in agents if name not in EMPTY_DIR_STOP]
    if unknown:
        print("rtk cleanup: unknown agent(s): %s" % ", ".join(unknown), file=sys.stderr)
        sys.exit(1)
    for name in agents:
        clean_agent(name)
