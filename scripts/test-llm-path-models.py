#!/usr/bin/env python3
"""Launch wrappers pick a model from the startup directory.

Expected models are the resolved llm.path_models entries, not a copied id.
"""

import atexit
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from _testlib import capture

root = Path(sys.argv[1]).resolve()
zsh = shutil.which("zsh")
assert zsh, "zsh is required"


def run(template, error=None):
    result = capture(root, ["execute-template"], stdin=template)
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


def configured_path_models():
    raw = run(
        '{{- $out := list -}}'
        '{{- range $rule := .llm.path_models -}}'
        '{{- $model := includeTemplate "llm/resolve-model-alias" (dict "model" $rule.model "aliases" $.llm.models) | trim -}}'
        '{{- $out = append $out (dict "paths" $rule.paths "model" $model) -}}'
        '{{- end -}}'
        '{{- $out | toJson -}}'
    )
    rules = json.loads(raw)
    assert rules, "llm.path_models is empty"
    return rules


def model_for(rules, keys):
    matches = [rule["model"] for rule in rules if keys in rule["paths"]]
    assert len(matches) == 1, (keys, rules)
    return matches[0]


def split_qualified(model):
    provider, sep, model_id = model.partition("/")
    assert sep and provider and model_id, model
    return provider, model_id


def goose_provider(provider):
    if provider in {"openai", "anthropic", "ollama", "openrouter"}:
        return provider
    return "custom_chezmoi_" + provider


qualified = "example/model"
fail([{"path": ["workspace", "iv"], "model": qualified}], "paths must be a list of path.toml key lists")
fail([{"paths": ["workspace", "iv"], "model": qualified}], "each paths entry must be a path.toml key list")
fail([{"paths": [["workspace", "missing"]], "model": qualified}], "unknown path workspace.missing")
fail([{"paths": [["chezmoi", "homeDir"]], "model": qualified}], "unknown path chezmoi.homeDir")
fail(
    [
        {"paths": [["workspace", "iv"]], "model": qualified},
        {"paths": [["workspace", "iv"]], "model": qualified},
    ],
    "duplicate prefix",
)
fail([{"paths": [["workspace", "iv"]], "model": "example/${missing_model}"}], "unknown alias")
fail([{"paths": [["workspace", "iv"]], "model": "bare-id"}], "must be alias/id")

pi = render("pi")
omp = render("omp")

rules = configured_path_models()
personal = model_for(rules, ["workspace", "personal"])
iv = model_for(rules, ["workspace", "iv"])
personal_provider, personal_id = split_qualified(personal)
# [chezmoi, workingTree] is the source passed to execute-template, not a
# path.toml location. CI checks out somewhere other than ~/.local/share/chezmoi.
working_tree = os.path.normpath(run("{{- .chezmoi.workingTree -}}").strip())
listing = zsh_eval(
    pi,
    r"""
print -r -- "count=$#PATH_MODEL_PREFIXES"
for (( i = 1; i <= $#PATH_MODEL_PREFIXES; i++ )); do
  print -r -- "$PATH_MODEL_PREFIXES[i] $PATH_MODEL_MODELS[i]"
done
""",
)
rows = dict(line.rsplit(" ", 1) for line in listing.splitlines() if line.startswith("/"))
chezmoi_matches = [prefix for prefix in rows if os.path.normpath(prefix) == working_tree]
assert chezmoi_matches, (working_tree, sorted(rows))
chezmoi_prefix = chezmoi_matches[0]
personal_prefix = next(prefix for prefix in rows if prefix.endswith("/Developer/Personal"))
# Later template renders stat this tree. Create it only for the cwd checks,
# and remove it again when this process made the empty directory.
if not Path(personal_prefix).exists():

    def remove_empty_created_tree() -> None:
        current = Path(personal_prefix)
        home = Path.home()
        while current != home and current.is_dir():
            try:
                current.rmdir()
            except OSError:
                return
            current = current.parent

    atexit.register(remove_empty_created_tree)
oss_prefix = next(prefix for prefix in rows if prefix.endswith("/Developer/OpenSource"))
iv_prefix = next(prefix for prefix in rows if prefix.endswith("/Developer/InfinityValley"))
assert rows[chezmoi_prefix] == personal
assert rows[personal_prefix] == personal
assert rows[oss_prefix] == personal
assert rows[iv_prefix] == iv
chosen = zsh_eval(
    pi,
    "show() { local found; found=$(path_model_for \"$1\"); print -r -- \"[$found]\"; }\n"
    + f"""
show {json.dumps(chezmoi_prefix + "/home")}
show {json.dumps(personal_prefix + "/blog")}
show {json.dumps(personal_prefix + "ity/blog")}
show {json.dumps(oss_prefix + "/luvus")}
show {json.dumps(iv_prefix + "/ivc")}
show /tmp
""",
).splitlines()
assert chosen == [f"[{personal}]", f"[{personal}]", "[]", f"[{personal}]", f"[{iv}]", "[]"]

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
path_model_skip --provider example; print -r -- $?
""",
)
assert pi_skip.splitlines() == ["0", "1 ", "0"]

opencode = render("opencode")
grok = render("grok")
goose = render("goose")
copilot = render("copilot")

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
if f"PATH_MODEL_COPILOT_URL[{personal_provider}]" in copilot:
    assert copilot_lines[:3] == ["0", "--model", personal_id]
    assert copilot_lines[3].startswith("https://")
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
grok_plan = zsh_eval(
    grok,
    f'path_model_for() {{ print -r -- {json.dumps(iv)}; }}\n'
    'path_model_plan\nprint -l -- "${PLAN_ARGS[@]}"\n',
)
assert grok_plan.splitlines()[:2] == ["--model", iv]

codex = render("codex")
codex_plan = zsh_eval(
    codex,
    "mkdir -p " + json.dumps(personal_prefix) + "\ncd " + json.dumps(personal_prefix) + r"""
path_model_plan 'fix the bug'
print -r -- "$PLAN_SKIP"
print -l -- "${PLAN_ARGS[@]}"
print -r -- "---"
path_model_plan exec resume last
print -r -- "$PLAN_SKIP"
print -r -- "---"
path_model_plan --model other
print -r -- "$PLAN_SKIP"
print -r -- "---"
path_model_plan -C /tmp exec elsewhere
print -r -- "$PLAN_SKIP"
print -l -- "${PLAN_ARGS[@]}"
print -r -- "---"
path_model_plan app
print -r -- "$PLAN_SKIP"
""",
)
codex_lines = codex_plan.splitlines()
separator = codex_lines.index("---")
launch, rest = codex_lines[:separator], codex_lines[separator + 1 :]
assert rest == ["1", "---", "1", "---", "0", "-C", "/tmp", "exec", "elsewhere", "---", "1"]
if f'path_model_codex_alias="{personal_provider}"' in codex:
    assert launch == [
        "0",
        "-c",
        f'model_provider="{personal_provider}"',
        "-c",
        f'model="{personal_id}"',
        "fix the bug",
    ]
else:
    assert launch == ["2", personal_provider]
yolo = zsh_eval(
    codex,
    r"""
PLAN_ARGS=(exec resume last)
path_model_bypass
print -l -- "${PLAN_ARGS[@]}"
print -r -- "---"
PLAN_ARGS=(--yolo login)
path_model_bypass
print -l -- "${PLAN_ARGS[@]}"
print -r -- "---"
PLAN_ARGS=(-- --yolo)
path_model_bypass
print -l -- "${PLAN_ARGS[@]}"
""",
)
assert yolo.splitlines() == [
    "--yolo",
    "exec",
    "resume",
    "last",
    "---",
    "--yolo",
    "login",
    "---",
    "--yolo",
    "--",
    "--yolo",
]


def bypass(tool, args):
    body = "PLAN_ARGS=(" + " ".join(json.dumps(arg) for arg in args) + ")\n"
    body += 'path_model_bypass\nprint -l -- "${PLAN_ARGS[@]}"\n'
    return zsh_eval(render(tool), body).splitlines()


assert bypass("omp", ["launch"])[:1] == ["--approval-mode=yolo"]
assert bypass("omp", ["--auto-approve", "launch"]) == ["--auto-approve", "launch"]
assert bypass("opencode", ["run", "x"])[:1] == ["--auto"]
assert bypass("grok", ["agent"])[:2] == ["--permission-mode", "bypassPermissions"]
assert bypass("grok", ["--permission-mode", "plan"]) == ["--permission-mode", "plan"]
assert bypass("copilot", []) == ["--yolo"]
assert bypass("pi", ["hi"]) == ["hi"]
goose_mode = zsh_eval(
    render("goose"),
    'unset GOOSE_MODE\npath_model_apply_defaults\nprint -r -- "$GOOSE_MODE"\n'
    'GOOSE_MODE=ask\npath_model_apply_defaults\nprint -r -- "$GOOSE_MODE"\n',
)
assert goose_mode.splitlines() == ["auto", "ask"]

assert goose_plan.splitlines() == [
    "0",
    "session",
    "--provider",
    goose_provider(personal_provider),
    "--model",
    personal_id,
    "fix the bug",
    "---",
    "1",
    "session",
    "list",
    "---",
    "1",
]
