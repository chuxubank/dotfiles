#!/usr/bin/env python3

import importlib.util
import json
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
    hooks.write_text(json.dumps({
        "version": 1,
        "hooks": {
            "event": [
                {"command": "owned hook"},
                {"command": "keep hook"},
            ]
        },
    }))
    owned = home / ".agent/owned.js"
    owned.write_text("owned")
    block = home / ".agent/config.toml"
    block.write_text("keep = true\n# begin owner\nremove = true\n# end owner\nafter = true\n")
    cleanup = {
        "needles": ["owned"],
        "standalone": {"agent": [".agent/owned.js"]},
        "json_hooks": {"agent": [".agent/hooks.json"]},
        "managed_blocks": [{
            "path": ".agent/config.toml",
            "start": "# begin owner",
            "end": "# end owner",
        }],
    }
    engine.clean_targets(cleanup, ["agent"], roots, extras=True)
    data = json.loads(hooks.read_text())
    assert data["hooks"]["event"] == [{"command": "keep hook"}]
    assert not owned.exists()
    text = block.read_text()
    assert "remove" not in text and "keep = true" in text and "after = true" in text

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

print("ok integration engine")
