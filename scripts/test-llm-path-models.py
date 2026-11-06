#!/usr/bin/env python3
"""Launch wrappers pick a model from the startup directory."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
zsh = shutil.which("zsh")
assert zsh, "zsh is required"
command = ["chezmoi"]
for flag, key in (("--persistent-state", "CHEZMOI_VERIFY_STATE"), ("--cache", "CHEZMOI_VERIFY_CACHE")):
    if os.environ.get(key):
        command.extend([flag, os.environ[key]])
command.extend(["execute-template", "--source", str(root)])


def run(template, error=None):
    result = subprocess.run(command, input=template, text=True, capture_output=True)
    if error:
        assert result.returncode != 0 and error in result.stderr, result.stderr
        return ""
    assert result.returncode == 0, result.stderr
    return result.stdout


def render(tool):
    template = (
        '{{- includeTemplate "llm/path-model-wrapper" (mergeOverwrite (deepCopy .) (dict "tool" '
        + json.dumps(tool)
        + ")) -}}"
    )
    return run(template)


def fail(path_models, message):
    payload = json.dumps(json.dumps(path_models))
    template = (
        '{{- $ctx := deepCopy . -}}'
        '{{- $_ := set $ctx.llm "path_models" (' + payload + " | fromJson) -}}"
        '{{- includeTemplate "llm/path-model-wrapper" (mergeOverwrite $ctx (dict "tool" "pi")) -}}'
    )
    run(template, message)


def zsh_eval(script, body):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "wrapper.zsh"
        path.write_text(script)
        result = subprocess.run([zsh, "-f", "-c", f"source {path}\n{body}"], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    return result.stdout


fail([{"path": "Developer/Personal", "model": "iv-codex/gpt-6.1-sol"}], "path must be a path.toml key list")
fail([{"path": ["workspace", "missing"], "model": "iv-codex/gpt-6.1-sol"}], "unknown path workspace.missing")
fail(
    [
        {"path": ["workspace", "iv"], "model": "iv-codex/${gpt_primary}"},
        {"path": ["workspace", "iv"], "model": "iv-codex/${gpt_primary}"},
    ],
    "duplicate prefix",
)
fail([{"path": ["workspace", "iv"], "model": "iv-codex/${missing_model}"}], "unknown alias")
fail([{"path": ["workspace", "iv"], "model": "gpt-6.1-sol"}], "must be alias/id")

pi = render("pi")
omp = render("omp")
subprocess.run([zsh, "-n", "-c", pi], check=True)
subprocess.run([zsh, "-n", "-c", omp], check=True)

personal = "magpie/grok/grok-4.7-build-fast@500k"
iv = "iv-codex/gpt-6.1-sol"
for script in (pi, omp):
    assert personal in script and iv in script
    listing = zsh_eval(
        script,
        r"""
print -r -- "count=$#PATH_MODEL_PREFIXES"
for (( i = 1; i <= $#PATH_MODEL_PREFIXES; i++ )); do
  print -r -- "$PATH_MODEL_PREFIXES[i] $PATH_MODEL_MODELS[i]"
done
""",
    )
    rows = dict(line.rsplit(" ", 1) for line in listing.splitlines() if line.startswith("/"))
    personal_prefix = next(prefix for prefix in rows if prefix.endswith("/Developer/Personal"))
    iv_prefix = next(prefix for prefix in rows if prefix.endswith("/Developer/InfinityValley"))
    assert rows[personal_prefix] == personal
    assert rows[iv_prefix] == iv
    chosen = zsh_eval(
        script,
        "show() { local found; found=$(path_model_for \"$1\"); print -r -- \"[$found]\"; }\n"
        + f"""
show {json.dumps(personal_prefix + "/blog")}
show {json.dumps(personal_prefix + "ity/blog")}
show {json.dumps(iv_prefix + "/ivc")}
show /tmp
""",
    ).splitlines()
    assert chosen == [f"[{personal}]", "[]", f"[{iv}]", "[]"]

skip = zsh_eval(
    omp,
    r"""
check() { path_model_skip "$@"; print -r -- "$? $REPLY"; }
check
check --model other/model
check --continue
check -r abc123
check plugin list
check acp
check --cwd /tmp/work 'fix the bug'
check -- 'plugin should stay a message'
""",
)
assert skip.splitlines() == [
    "1 ",
    "0 ",
    "0 ",
    "0 ",
    "0 ",
    "1 ",
    "1 /tmp/work",
    "1 ",
]

pi_skip = zsh_eval(
    pi,
    r"""
path_model_skip install pkg; print -r -- $?
path_model_skip 'fix the bug'; print -r -- "$? $REPLY"
path_model_skip --provider iv-codex; print -r -- $?
""",
)
assert pi_skip.splitlines() == ["0", "1 ", "0"]

opencode = render("opencode")
grok = render("grok")
goose = render("goose")
copilot = render("copilot")
for script in (opencode, grok, goose, copilot):
    subprocess.run([zsh, "-n", "-c", script], check=True)

assert "iv-codex/gpt-6.1-sol" in opencode
assert "openai/gpt-6.1-sol" not in opencode
assert personal in opencode
assert "github-copilot/gpt-6.1-sol" in grok and "grok/grok-4.7-build-fast@500k" in grok
assert "iv-codex/gpt-6.1-sol" in copilot
assert personal in copilot
assert "COPILOT_PROVIDER_BASE_URL" in copilot
# iv and magpie are off on a ci host, so their auth commands are absent.
if "codex-auth-token" in copilot or "gateway-key" in copilot:
    assert "pass-field" in copilot
assert "custom_chezmoi_iv-codex" in goose and "gpt-6.1-sol" in goose
assert "custom_chezmoi_magpie" in goose and "grok/grok-4.7-build-fast@500k" in goose

copilot_plan = zsh_eval(
    copilot,
    "mkdir -p " + json.dumps(personal_prefix) + "\ncd " + json.dumps(personal_prefix) + r"""
path_model_plan
print -r -- "$PLAN_SKIP"
print -l -- "${PLAN_ARGS[@]}"
if [[ -n $PATH_MODEL_COPILOT_ALIAS ]]; then
  print -r -- "$PATH_MODEL_COPILOT_URL[$PATH_MODEL_COPILOT_ALIAS]"
  print -r -- "$PATH_MODEL_COPILOT_AUTH[$PATH_MODEL_COPILOT_ALIAS]"
fi
""",
)
copilot_lines = copilot_plan.splitlines()
if "PATH_MODEL_COPILOT_URL[magpie]" in copilot:
    assert copilot_lines[:3] == ["0", "--model", "grok/grok-4.7-build-fast@500k"]
    assert copilot_lines[3].startswith("https://magpie.")
    assert "pass-field" in copilot_lines[4] and "gateway-key" in copilot_lines[4]
else:
    assert copilot_lines == ["2", personal]

opencode_skip = zsh_eval(
    opencode,
    r"""
path_model_skip models; print -r -- $?
path_model_skip acp; print -r -- "$? $REPLY"
path_model_skip /tmp/work; print -r -- "$? $REPLY"
path_model_skip -m other/model; print -r -- $?
""",
)
assert opencode_skip.splitlines() == ["0", "1 ", "1 /tmp/work", "0"]

grok_skip = zsh_eval(
    grok,
    r"""
path_model_skip --cwd /tmp/work; print -r -- "$? $REPLY"
path_model_skip plugin; print -r -- $?
path_model_skip agent 'do it'; print -r -- "$? $REPLY"
""",
)
assert grok_skip.splitlines() == ["1 /tmp/work", "0", "1 "]

goose_plan = zsh_eval(
    goose,
    "mkdir -p " + json.dumps(personal_prefix) + "\ncd " + json.dumps(personal_prefix) + r"""
path_model_plan session 'fix the bug'
print -r -- "$PLAN_SKIP"
print -l -- "${PLAN_ARGS[@]}"
print -r -- "---"
path_model_plan session list
print -r -- "$PLAN_SKIP"
print -l -- "${PLAN_ARGS[@]}"
print -r -- "---"
path_model_plan update
print -r -- "$PLAN_SKIP"
""",
)
assert goose_plan.splitlines() == [
    "0",
    "session",
    "--provider",
    "custom_chezmoi_magpie",
    "--model",
    "grok/grok-4.7-build-fast@500k",
    "fix the bug",
    "---",
    "1",
    "session",
    "list",
    "---",
    "1",
]
