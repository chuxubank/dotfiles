#!/usr/bin/env python3

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

root = Path(sys.argv[1])
engine_path = root / "home/.chezmoitemplates/plugins/engine.py"
spec = importlib.util.spec_from_file_location("plugin_engine", engine_path)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)

with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp)
    engine.HOME = home
    bin_dir = home / "bin"
    bin_dir.mkdir()
    state = home / "state.json"
    log = home / "commands.log"
    state.write_text(json.dumps({"plugins": [{"name": "keep", "enabled": True}]}))
    fake = bin_dir / "fake-plugin"
    fake.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "state=Path(os.environ['PLUGIN_STATE'])\n"
        "log=Path(os.environ['PLUGIN_LOG'])\n"
        "data=json.loads(state.read_text())\n"
        "args=sys.argv[1:]\n"
        "if args == ['list']:\n"
        " print(json.dumps(data))\n"
        "elif args[:1] == ['install']:\n"
        " data['plugins'].append({'name': args[1], 'enabled': True})\n"
        " state.write_text(json.dumps(data)); log.open('a').write('install '+args[1]+'\\n')\n"
        "elif args[:1] == ['remove']:\n"
        " data['plugins']=[p for p in data['plugins'] if p['name'] != args[1]]\n"
        " state.write_text(json.dumps(data)); log.open('a').write('remove '+args[1]+'\\n')\n"
        "else:\n"
        " raise SystemExit(2)\n"
    )
    fake.chmod(0o755)
    old_path = os.environ["PATH"]
    os.environ["PATH"] = str(bin_dir) + os.pathsep + old_path
    os.environ["PLUGIN_STATE"] = str(state)
    os.environ["PLUGIN_LOG"] = str(log)
    manager = {
        "name": "fake",
        "label": "Fake",
        "binary": "fake-plugin",
        "identity": "name",
        "inventory": {
            "command": ["fake-plugin", "list"],
            "path": ["plugins"],
            "mode": "field",
            "field": ["name"],
            "enabled_field": ["enabled"],
            "label": "fake plugins",
        },
        "install": ["fake-plugin", "install", "{name}"],
        "uninstall": ["fake-plugin", "remove", "{installed}"],
        "declared_plugins": [
            {"name": "keep", "source": "keep-source", "enabled": True},
            {"name": "missing", "source": "missing-source", "enabled": True},
            {"name": "disabled", "source": "disabled-source", "enabled": False},
        ],
        "declared_marketplaces": [],
    }
    try:
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            engine.reconcile(manager)
        output = stdout.getvalue()
        assert "Install Fake plugin: missing" in output
        assert "disabled" not in output
        assert log.read_text() == "install missing\n"

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            engine.reconcile(manager)
        assert stdout.getvalue() == ""
        assert log.read_text() == "install missing\n"

        settings = home / "settings.json"
        settings.write_text(json.dumps({"packages": ["keep", "stale-before"]}))
        manager["cleanup_order"] = "before"
        manager["cleanup_inventory"] = {
            "file": "settings.json",
            "path": ["packages"],
            "mode": "string_or_field",
            "field": ["source"],
            "label": "old packages",
        }
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            engine.reconcile(manager)
        assert "Remove undeclared Fake plugin: stale-before" in stdout.getvalue()
        assert log.read_text().endswith("remove stale-before\n")
        manager.pop("cleanup_order")
        manager.pop("cleanup_inventory")

        cleanup_only = {
            "name": "fake",
            "label": "Fake",
            "binary": "fake-plugin",
            "identity": "name",
            "cleanup_order": "before",
            "cleanup_inventory": {
                "file": "settings.json",
                "path": ["packages"],
                "mode": "string_or_field",
                "field": ["source"],
                "label": "old packages",
            },
            "uninstall": ["fake-plugin", "remove", "{installed}"],
            "declared_plugins": [
                {"name": "keep", "source": "keep-source", "enabled": True},
                {"name": "never-installed", "source": "never-source", "enabled": True},
            ],
            "declared_marketplaces": [],
        }
        settings.write_text(json.dumps({"packages": ["keep", "stale-only"]}))
        before = log.read_text()
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            engine.reconcile(cleanup_only)
        assert "Remove undeclared Fake plugin: stale-only" in stdout.getvalue()
        assert "Install" not in stdout.getvalue()
        assert log.read_text() == before + "remove stale-only\n"

        data = json.loads(state.read_text())
        data["plugins"].append({"name": "stale", "enabled": True})
        state.write_text(json.dumps(data))
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            engine.reconcile(manager)
        assert "Remove undeclared Fake plugin: stale" in stdout.getvalue()
        assert log.read_text().endswith("remove stale\n")

        manager["inventory"]["command"] = ["fake-plugin", "broken"]
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                engine.reconcile(manager)
        except SystemExit as err:
            assert err.code == 1
        else:
            raise AssertionError("broken inventory did not fail closed")
        assert log.read_text().endswith("remove stale\n")
    finally:
        os.environ["PATH"] = old_path
        os.environ.pop("PLUGIN_STATE", None)
        os.environ.pop("PLUGIN_LOG", None)

with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp)
    engine.HOME = home
    protected = home / ".claude/settings.json"
    protected.parent.mkdir(parents=True)
    protected.write_text(json.dumps({"extraKnownMarketplaces": {"claude-owned": {}}}))
    inventory = {
        "path": [],
        "mode": "field",
        "field": ["name"],
        "source_fields": [["source", "url"]],
        "label": "marketplaces",
    }
    data = [
        {"name": "alias", "source": {"url": "https://desired.example/repo.git"}},
        {"name": "claude-owned", "source": {"url": "https://claude.example/repo.git"}},
        {"name": "stale", "source": {"url": "https://stale.example/repo.git"}},
    ]
    entries = []
    for item in data:
        name = engine.value_at(item, inventory["field"])
        entries.append(
            {
                "name": name,
                "enabled": True,
                "sources": [engine.value_at(item, inventory["source_fields"][0])],
            }
        )
    assert entries[0]["sources"] == ["https://desired.example/repo.git"]
    commands = []
    original_load = engine.load_inventory
    original_run = engine.run_command
    engine.load_inventory = lambda _inventory: entries
    engine.run_command = lambda template, values, quiet=False: commands.append(
        engine.command_args(template, values)
    ) or 0
    manager = {
        "label": "Fake",
        "declared_marketplaces": [
            {
                "name": "desired",
                "source": "https://desired.example/repo.git",
                "enabled": True,
            }
        ],
        "marketplaces": {
            "inventory": inventory,
            "install": ["market", "add", "{source}"],
            "uninstall": ["market", "remove", "{installed}"],
            "preserve": [
                {
                    "file": ".claude/settings.json",
                    "path": ["extraKnownMarketplaces"],
                }
            ],
        },
    }
    try:
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            assert not engine.reconcile_marketplaces(manager)
        assert stdout.getvalue() == "Remove undeclared Fake marketplace: stale\n"
        assert commands == [["market", "remove", "stale"]]

        commands.clear()
        protected.write_text("not json")
        try:
            engine.reconcile_marketplaces(manager)
        except engine.InventoryError:
            pass
        else:
            raise AssertionError("corrupt marketplace protection failed open")
        assert commands == []
    finally:
        engine.load_inventory = original_load
        engine.run_command = original_run

assert engine.command_args(
    ["herdr", "install", "{source}", "{ref_args}"],
    {"source": "owner/repo", "ref": "main"},
) == ["herdr", "install", "owner/repo", "--ref", "main"]
assert engine.command_args(
    ["herdr", "install", "{source}", "{ref_args}"],
    {"source": "owner/repo"},
) == ["herdr", "install", "owner/repo"]
npm_manager = {"identity": "source", "identity_transform": "npm_name"}
assert engine.resource_identity(npm_manager, {"source": "npm:package@1.2.3"}) == "npm:package"
assert (
    engine.resource_identity(npm_manager, {"source": "npm:@scope/package@1.2.3"})
    == "npm:@scope/package"
)
assert (
    engine.resource_identity(npm_manager, {"source": "npm:@scope/package"})
    == "npm:@scope/package"
)
assert engine.normalize_identity(npm_manager, "npm:package@1.2.3") == "npm:package"
assert engine.normalize_identity(npm_manager, "git:owner/repo") == "git:owner/repo"
pinned_manager = {
    **npm_manager,
    "label": "Pinned",
    "declared_plugins": [
        {"name": "package", "source": "npm:package@1.2.3", "enabled": True}
    ],
}
original_load = engine.load_inventory
original_run = engine.run_command
engine.load_inventory = lambda _inventory: [
    {"name": "npm:package@1.2.3", "enabled": True, "sources": []}
]
engine.run_command = lambda *_args, **_kwargs: (_ for _ in ()).throw(
    AssertionError("matching pinned package was removed")
)
try:
    assert not engine.cleanup_resources(pinned_manager, {}, ["remove"])
finally:
    engine.load_inventory = original_load
    engine.run_command = original_run

with tempfile.TemporaryDirectory() as tmp:
    engine.HOME = Path(tmp)
    settings = Path(tmp) / ".pi/agent/settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"packages": ["npm:one", {"source": "git:two"}]}))
    inventory = {
        "file": ".pi/agent/settings.json",
        "path": ["packages"],
        "mode": "string_or_field",
        "field": ["source"],
        "label": "pi packages",
    }
    assert [item["name"] for item in engine.load_inventory(inventory)] == [
        "npm:one",
        "git:two",
    ]

print("ok plugin engine")
