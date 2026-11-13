#!/usr/bin/env python3
"""Check skills reconciliation and the update shortcut without touching live installs."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
command = ["chezmoi"]
for flag, variable in (
    ("--persistent-state", "CHEZMOI_VERIFY_STATE"),
    ("--cache", "CHEZMOI_VERIFY_CACHE"),
):
    if os.environ.get(variable):
        command.extend([flag, os.environ[variable]])
command.extend(["execute-template", "--source", str(root)])

providers = [
    {"name": "direct", "source": "fixture/direct"},
    {"name": "nested", "source": "fixture/repo/plugins/deep/skills", "full_depth": True},
    {"name": ["*", "category-*", "category-a"], "source": "fixture/repo/categories"},
    {"name": "download", "source": "https://fixture.invalid/SKILL.md"},
]
prefix = (
    '{{- $_ := set . "skills" (dict "agents" (list "fixture-agent") '
    '"provider_groups" (dict "test" (' + json.dumps(json.dumps(providers)) + ' | fromJson))) -}}'
    '{{- $_ := set .tools "fixture-owner" (dict) -}}'
)


def render(source):
    return subprocess.run(
        command, input=prefix + source, text=True, capture_output=True, check=True
    ).stdout


setup = render((root / "home/.chezmoiscripts/run_onchange_after_200_setup-skills.sh.tmpl").read_text())
zshrc = render((root / "home/dot_zshrc.tmpl").read_text())
# Execute only this alias, never the rest of the user's shell initialization.
shortcut = next((line for line in zshrc.splitlines() if line.startswith("alias ups=")), None)
assert shortcut, "ups must delegate update selection to the CLI rather than parsing its private lock"

with tempfile.TemporaryDirectory() as tmp:
    sandbox = Path(tmp)
    bins = sandbox / render('{{ .path.tool.bun }}').strip() / "bin"
    bins.mkdir(parents=True)
    for name in ("jq", "mktemp", "rm", "mv", "cat", "sed"):
        (bins / name).symlink_to(shutil.which(name))
    stub = bins / "skills"
    stub.write_text('''#!/usr/bin/env python3
import json
import os
import sys

args = sys.argv[1:]
with open(os.environ["MOCK_LOG"], "a") as log:
    log.write(json.dumps(args) + "\\n")
names = ["direct", "nested", "category-a", "category-b", "download", "external", "undeclared"]
mode = os.environ.get("MOCK_MODE", "ok")
if args[0] == "list":
    if mode == "inventory-failure":
        sys.exit(8)
    if mode in ("missing", "install-failure"):
        names.remove("nested")
    if mode == "missing-category":
        names.remove("category-b")
    if mode == "invalid-agent" and "--agent" in args:
        print("{}")
    else:
        print(json.dumps([{"path": "/fixture/" + name} for name in names] + [{"path": None}]))
elif args[0] == "add" and "--list" in args:
    if mode == "resolve-failure":
        sys.exit(9)
    print("│    category-a\\n│    category-b")
elif args[0] == "add":
    if mode == "install-failure":
        sys.exit(10)
elif args[0] == "update":
    sys.exit(int(os.environ.get("MOCK_UPDATE_STATUS", "0")))
elif args[0] != "remove":
    raise AssertionError(args)
'''.replace("#!/usr/bin/env python3", "#!" + sys.executable))
    stub.chmod(0o755)
    script = sandbox / "setup.zsh"
    script.write_text(setup)
    subprocess.run(["zsh", "-n", str(script)], check=True)
    log = sandbox / "calls.jsonl"
    env = {"HOME": str(sandbox), "PATH": str(bins), "MOCK_LOG": str(log)}
    # Declare an externally installed skill through the real external resolver.
    # Fixture injection is local to this rendered script.
    script.write_text(render(
        '{{- $_ := set .skills "external" (list (dict "name" "external" "owner" "fixture-owner")) -}}'
        + (root / "home/.chezmoiscripts/run_onchange_after_200_setup-skills.sh.tmpl").read_text()
    ))

    def run(mode="ok", update_status="0"):
        log.unlink(missing_ok=True)
        result = subprocess.run(
            [shutil.which("zsh"), "-f", str(script)],
            env={**env, "MOCK_MODE": mode, "MOCK_UPDATE_STATUS": update_status},
            text=True, capture_output=True, check=False,
        )
        calls = [json.loads(line) for line in log.read_text().splitlines()]
        return result, calls

    result, calls = run()
    assert result.returncode == 0, result.stderr
    expected = ["update", "-g", "direct", "nested", "category-a", "category-b", "download"]
    assert expected in calls, calls
    assert ["remove", "undeclared", "-g", "--yes"] in calls, calls
    assert not any(call[0] == "remove" and "external" in call for call in calls), calls
    assert not any(call[0] == "add" and "--list" not in call for call in calls), calls

    result, calls = run("missing")
    assert result.returncode == 0, result.stderr
    assert ["add", "fixture/repo/plugins/deep/skills", "--global", "--yes",
            "--full-depth", "--skill", "nested", "--agent", "fixture-agent"] in calls, calls
    result, calls = run("missing-category")
    assert result.returncode == 0, result.stderr
    assert ["add", "fixture/repo/categories", "--global", "--yes",
            "--skill", "category-a", "--skill", "category-b", "--agent", "fixture-agent"] in calls, calls
    assert expected in calls, "overlapping selectors must not duplicate update names"
    assert sum(call[0] == "list" and "--agent" in call for call in calls) == 1, calls
    for mode in ("inventory-failure", "resolve-failure", "install-failure", "invalid-agent"):
        result, calls = run(mode)
        assert result.returncode != 0, (mode, result.stderr)
        assert not any(call[0] == "remove" for call in calls), calls
    result, calls = run(update_status="7")
    assert result.returncode != 0, result.stderr
    result, calls = run()
    assert result.returncode == 0 and expected in calls, "update failure must retry"
    script.write_text(render(
        '{{- $_ := set .skills "provider_groups" (dict) -}}'
        + (root / "home/.chezmoiscripts/run_onchange_after_200_setup-skills.sh.tmpl").read_text()
    ))
    result, calls = run()
    assert result.returncode == 0, result.stderr
    assert not any(call[0] == "update" for call in calls), "empty selection must not update everything"

    # Alias forwards scope, selected names and exit status without interpreting locks.
    short_script = sandbox / "shortcut.zsh"
    short_script.write_text(shortcut + '\nups nested\n')
    log.unlink()
    result = subprocess.run(
        [shutil.which("zsh"), "-f", str(short_script)],
        env={**env, "MOCK_UPDATE_STATUS": "7"}, capture_output=True, check=False,
    )
    assert result.returncode == 7, result.stderr
    assert json.loads(log.read_text()) == ["update", "-g", "nested"]

print("ok skills: nested/URL/wildcard updates, external ownership, cleanup guards, retry and shortcut")
