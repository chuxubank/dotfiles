#!/usr/bin/env python3

import contextlib
import importlib.util
import io
import json
import stat
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

root = Path(sys.argv[1])
engine_path = root / "home/.chezmoitemplates/integrations/engine.py"
spec = importlib.util.spec_from_file_location("integration_engine", engine_path)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)

with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp)
    engine.HOME = home
    roots = {"agent": ".agent"}
    hooks = home / ".agent/hooks.json"
    hooks.parent.mkdir(parents=True)
    hooks.write_text(
        json.dumps(
            {
                "version": 1,
                "hooks": {
                    "event": [
                        {"command": "owned hook"},
                        {"command": "keep hook"},
                    ]
                },
            }
        )
    )
    owned = home / ".agent/owned.js"
    owned.write_text("owned")
    block = home / ".agent/config.toml"
    block.write_text(
        "keep = true\n# begin owner\nremove = true\n# end owner\nafter = true\n"
    )
    cleanup = {
        "needles": ["owned"],
        "standalone": {"agent": [".agent/owned.js"]},
        "json_hooks": {"agent": [".agent/hooks.json"]},
        "managed_blocks": [
            {
                "path": ".agent/config.toml",
                "start": "# begin owner",
                "end": "# end owner",
            }
        ],
    }
    engine.clean_targets(cleanup, ["agent"], roots, extras=True)
    data = json.loads(hooks.read_text())
    assert data["hooks"]["event"] == [{"command": "keep hook"}]
    assert not owned.exists()
    text = block.read_text()
    assert "remove" not in text and "keep = true" in text and "after = true" in text
    mode_path = home / ".agent/mode.txt"
    mode_path.write_text("before")
    mode_path.chmod(0o640)
    engine.atomic_write_text(mode_path, "after")
    assert mode_path.read_text() == "after"
    assert stat.S_IMODE(mode_path.stat().st_mode) == 0o640
    try:
        engine.home_path("../escape")
    except ValueError:
        pass
    else:
        raise AssertionError("parent traversal was accepted")

with tempfile.TemporaryDirectory() as tmp:
    engine.HOME = Path(tmp)
    roots = {"agent": ".agent"}
    cleanup = {"standalone": {"agent": [".agent/owned.js"]}}
    teardown = {
        "owner": "owner",
        "lifecycle": {"label": "Owner", "cleanup": cleanup},
        "targets": [{"tool": "agent", "enabled": False, "args": []}],
    }
    with contextlib.redirect_stdout(io.StringIO()) as stdout:
        engine.reconcile(teardown, "teardown", roots)
    assert stdout.getvalue() == ""

    owned = Path(tmp) / ".agent/owned.js"
    owned.parent.mkdir(parents=True)
    owned.write_text("owned")
    with contextlib.redirect_stdout(io.StringIO()) as stdout:
        engine.reconcile(teardown, "teardown", roots)
    output = stdout.getvalue()
    assert "Teardown Owner" in output and "removed" in output

    setup = {
        "owner": "owner",
        "lifecycle": {
            "label": "Owner",
            "binary": "integration-test-missing-binary",
            "cleanup": cleanup,
        },
        "targets": [{"tool": "agent", "enabled": True, "args": []}],
    }
    with contextlib.redirect_stdout(io.StringIO()) as stdout:
        engine.reconcile(setup, "setup", roots)
    assert stdout.getvalue() == ""

with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp)
    engine.HOME = home
    roots = {"agent": ".agent"}
    source = home / ".agent/hooks/pre/plugin.ts"
    source.parent.mkdir(parents=True)
    source.write_text("OldType from old-package\n")
    lifecycle = {
        "post_install": {
            "agent": {
                "move": {
                    "from": ".agent/hooks/pre/plugin.ts",
                    "to": ".agent/extensions/plugin.ts",
                },
                "replacements": [
                    ["OldType", "NewType"],
                    ["old-package", "new-package"],
                ],
            }
        }
    }
    engine.post_install(lifecycle, {"tool": "agent"}, roots)
    target = home / ".agent/extensions/plugin.ts"
    assert target.read_text() == "NewType from new-package\n"
    assert not source.exists()

    source.unlink(missing_ok=True)
    with contextlib.redirect_stdout(io.StringIO()) as stdout:
        engine.post_install(lifecycle, {"tool": "agent"}, roots)
    assert stdout.getvalue() == ""

with tempfile.TemporaryDirectory() as tmp:
    engine.HOME = Path(tmp)
    roots = {"agent": ".agent"}
    marker = Path(tmp) / ".agent/plugin.ts"
    counter = Path(tmp) / "installs"
    install_script = (
        "from pathlib import Path; "
        f"p=Path({str(marker)!r}); p.parent.mkdir(parents=True, exist_ok=True); "
        "p.write_text('installed'); "
        f"c=Path({str(counter)!r}); c.write_text(c.read_text()+'x' if c.exists() else 'x')"
    )
    setup = {
        "owner": "owner",
        "lifecycle": {
            "label": "Owner",
            "binary": sys.executable,
            "install": [sys.executable, "-c", install_script],
        },
        "targets": [
            {
                "tool": "agent",
                "enabled": True,
                "args": [],
                "installed": {"path": ".agent/plugin.ts"},
            }
        ],
    }
    engine.reconcile(setup, "setup", roots)
    assert counter.read_text() == "x"
    with contextlib.redirect_stdout(io.StringIO()) as stdout:
        engine.reconcile(setup, "setup", roots)
    assert stdout.getvalue() == ""
    assert counter.read_text() == "x"

with tempfile.TemporaryDirectory() as tmp:
    engine.HOME = Path(tmp)
    lifecycle = {
        "install": [sys.executable, "-c", "import time; time.sleep(2)"],
        "timeout_seconds": 1,
    }
    with contextlib.redirect_stderr(io.StringIO()) as stderr:
        code = engine.run_command(lifecycle, "install", {"tool": "agent", "args": []})
    assert code == 124
    assert "timed out" in stderr.getvalue()

print("ok integration engine")
