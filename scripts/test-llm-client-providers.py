#!/usr/bin/env python3
"""Offline native rendering and Goose provider-file synchronization checks."""

import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
command = ["chezmoi"]
for flag, key in (("--persistent-state", "CHEZMOI_VERIFY_STATE"), ("--cache", "CHEZMOI_VERIFY_CACHE")):
    if os.environ.get(key):
        command.extend([flag, os.environ[key]])
command.extend(["execute-template", "--source", str(root)])
base = {
    "models": {},
    "default_providers": ["gateway", "second"],
    "providers": {
        "gateway": {
            "name": "Gateway", "base_url": "https://gateway.example",
            "api_types": ["openai", "anthropic"],
            "models": ["vendor/model"],
            "auth": {"path": "Test/Gateway", "field": "gateway-key"},
        },
        "second": {"base_url": "https://second.example", "models": ["another/model"]},
        "google": {"type": "gemini", "models": [], "base_url": "https://google.example"},
        "openrouter": {"base_url": "https://openrouter.example"},
    },
    "tools": {
        "aider": {"model": "gemini/native", "supported_provider_types": ["openai", "anthropic", "gemini", "ollama"]},
        "goose": {"model": "openrouter/vendor/model", "supported_provider_types": ["openai", "anthropic", "ollama"], "providers": ["openrouter"]},
        "claude-code": {"model": "opusplan", "supported_provider_types": ["anthropic"]},
    },
}


def render(path, llm, home, yaml=False, enabled=True, stdin=None):
    source = (root / path).read_text()
    data = {
        "llm": llm,
        "chezmoi": {"homeDir": str(home), "stdin": stdin or "{}"},
        "host_env": "ci",
        "isDarkMode": True,
        "mcp": {"providers": [{
            "name": "fixture", "description": "Offline fixture",
            "when": {"enabled": True},
            "execution": {"type": "stdio", "cmd": "not-executed"},
        }]},
        "tools": {"goose": {"when": {"enabled": enabled}}},
    }
    # Replace LLM/MCP data outright so no live catalogs or auth are consulted.
    prefix = (
        '{{- $ctx := deepCopy . -}}{{- $_ := set $ctx "llm" (dict) -}}'
        '{{- $_ := set $ctx "mcp" (dict) -}}{{- $_ := set $ctx "tools" (dict) -}}'
        '{{- $ctx = mergeOverwrite $ctx (' + json.dumps(json.dumps(data)) + ' | fromJson) -}}'
    )
    template = prefix + '{{- $ := $ctx -}}{{- with $ctx -}}' + source + '{{- end -}}'
    result = subprocess.run(command, input=template, text=True, capture_output=True, env={**os.environ, "CI": "true"})
    assert result.returncode == 0, result.stderr
    if yaml:
        # Parse as a map, wrapping lists, without requiring PyYAML on CI.
        document = "value:\n" + "\n".join("  " + line for line in result.stdout.splitlines())
        template = "{{ (" + json.dumps(document) + " | fromYaml).value | toJson }}"
        result = subprocess.run(command, input=template, text=True, capture_output=True, env={**os.environ, "CI": "true"})
        assert result.returncode == 0, result.stderr
    return result.stdout


with tempfile.TemporaryDirectory() as tmp:
    home = Path(tmp)
    # Rich discovery must survive the native Pi/OMP render, not just id/name.
    model_cache = home / ".cache/llm/models/magpie.json"
    model_cache.parent.mkdir(parents=True)
    rows = [{
        "id": "auto/model@wide", "display_name": "Gateway model",
        "context_window": 500000, "max_output_tokens": 32000,
        "modalities": {"input": ["text", "image"]}, "reasoning": True,
        "reasoning_levels": ["low", "high", "xhigh"],
        "pricing": {"prompt": "0.000002", "completion": "0.000006",
                    "input_cache_read": "0.0000005", "input_cache_write": "0.000003"},
    }, {
        "id": "vendor/supported-levels", "context_length": 240000,
        "reasoning": True, "supported_reasoning_levels": [{"effort": "high"}],
    }, {"id": "vendor/bare"}]
    model_cache.write_text(json.dumps({"data": rows}))
    discovered = {
        "models": {},
        "default_providers": ["magpie"],
        "providers": {"magpie": {
            "base_url": "https://offline.invalid", "models_cache": "magpie-models-api",
        }},
        "tools": {"pi": {}, "omp": {}},
    }
    for tool, path, yaml in (
        ("pi", "home/dot_pi/private_agent/models.json.tmpl", False),
        ("omp", "home/dot_omp/private_agent/models.yml.tmpl", True),
    ):
        cfg = json.loads(render(path, discovered, home, yaml=yaml))
        models = {m["id"]: m for m in cfg["providers"]["magpie"]["models"]}
        model = models["auto/model@wide"]
        assert model["id"] == "auto/model@wide" and model["name"] == "Gateway model"
        assert model["contextWindow"] == 500000, model
        assert model["maxTokens"] == 32000, model
        assert model["input"] == ["text", "image"] and model["reasoning"] is True, model
        assert model["cost"] == {"input": 2, "output": 6, "cacheRead": 0.5, "cacheWrite": 3}, model
        if tool == "pi":
            assert model["thinkingLevelMap"]["xhigh"] == "xhigh", model
            assert model["thinkingLevelMap"]["medium"] is None, model
        else:
            assert model["thinking"]["efforts"] == ["low", "high", "xhigh"], model
        alternative = models["vendor/supported-levels"]
        assert alternative["contextWindow"] == 240000, alternative
        bare = models["vendor/bare"]
        assert bare["name"] == "vendor/bare" and bare["reasoning"] is False, bare
        assert bare["contextWindow"] == 128000 and bare["input"] == ["text"], bare
        assert "thinkingLevelMap" not in bare and "thinking" not in bare, bare

        # Explicit metadata overrides still win over discovery.
        overridden = copy.deepcopy(discovered)
        overridden["tools"][tool]["providers"] = {"magpie": {"model_overrides": {
            "auto/model@wide": {"limit": {"context": 300000}, "reasoning": False},
        }}}
        cfg = json.loads(render(path, overridden, home, yaml=yaml))
        model = next(m for m in cfg["providers"]["magpie"]["models"] if m["id"] == "auto/model@wide")
        assert model["contextWindow"] == 300000 and model["maxTokens"] == 32000, model
        assert model["reasoning"] is False and "thinkingLevelMap" not in model and "thinking" not in model

    # Name-only consumers retain their existing contract.
    template = '{{ includeTemplate "llm/fetch-models" (dict "type" "openai" "base_url" "https://offline.invalid" "auth_key" "" "cache_file" ' + json.dumps(str(model_cache)) + ') }}'
    names = subprocess.run(command, input=template, text=True, capture_output=True)
    assert names.returncode == 0, names.stderr
    assert json.loads(names.stdout) == {row["id"]: row.get("display_name", row["id"]) for row in rows}

    llm = copy.deepcopy(base)
    # Model-scoped routing means two inherited OpenAI endpoints never overwrite
    # a single global base/key. Provider prefixes in the upstream id survive.
    settings_path = "home/private_dot_aider.model.settings.yml.tmpl"
    settings = {entry["name"]: entry["extra_params"] for entry in json.loads(render(settings_path, llm, home, yaml=True))}
    assert settings["gateway/vendor/model"]["model"] == "vendor/model"
    assert settings["gateway/vendor/model"]["api_base"] == "https://gateway.example/v1"
    assert settings["second/another/model"]["api_base"] == "https://second.example/v1"

    # Goose retains the explicitly selected native provider, not the last
    # alphabetic provider in its inherited map.
    goose_config = "home/.chezmoitemplates/agent/goose.yaml"
    cfg = json.loads(render(goose_config, llm, home, yaml=True))
    assert cfg["GOOSE_PROVIDER"] == "openrouter" and cfg["GOOSE_MODEL"] == "vendor/model"
    llm["tools"]["goose"]["model"] = "gateway/vendor/model"
    cfg = json.loads(render(goose_config, llm, home, yaml=True))
    assert cfg["GOOSE_PROVIDER"] == "custom_chezmoi_gateway"
    assert cfg["GOOSE_MODEL"] == "vendor/model"

    sync_path = "home/.chezmoiscripts/run_onchange_after_955_sync-goose-providers.py.tmpl"
    script = home / "sync.py"
    script.write_text(render(sync_path, llm, home))
    subprocess.run([sys.executable, "-W", "error", "-m", "py_compile", str(script)], check=True)
    directory = home / ".config/goose/custom_providers"
    directory.mkdir(parents=True)
    user = directory / "user.json"
    user.write_text('{"user": true}')
    subprocess.run([sys.executable, str(script)], check=True)
    gateway = json.loads((directory / "custom_chezmoi_gateway.json").read_text())
    assert gateway["engine"] == "openai"
    assert gateway["base_url"] == "https://gateway.example/v1/chat/completions"
    assert gateway["auth"] == {"command": str(home / "bin/pass-field"), "args": ["Test/Gateway", "gateway-key"]}
    assert "api_key_env" not in gateway and gateway["dynamic_models"] is True
    assert (directory / "custom_chezmoi_gateway.json").stat().st_mode & 0o777 == 0o600
    subprocess.run([sys.executable, str(script)], check=True)
    # Make a write fail: the sync exits nonzero and can be retried; user files
    # are untouched. No real Goose process or authentication command is run.
    target = directory / "custom_chezmoi_gateway.json"
    target.unlink()
    target.mkdir()
    assert subprocess.run([sys.executable, str(script)], capture_output=True).returncode != 0
    target.rmdir()
    subprocess.run([sys.executable, str(script)], check=True)
    script.write_text(render(sync_path, llm, home, enabled=False))
    subprocess.run([sys.executable, str(script)], check=True)
    assert list(directory.iterdir()) == [user]
    assert user.read_text() == '{"user": true}'

    # CC has no registry. Inheritance must not hijack a native/login model;
    # explicitly qualified models select exactly one compatible endpoint.
    cc_path = "home/dot_claude/modify_settings.json"
    cfg = json.loads(render(cc_path, llm, home))
    assert "ANTHROPIC_BASE_URL" not in cfg["env"] and cfg["model"] == "opusplan"
    native = copy.deepcopy(llm)
    native["providers"]["native"] = {"type": "anthropic", "base_url": "https://native.example"}
    native["tools"]["claude-code"]["providers"] = {"anthropic": {"provider": "native"}}
    cfg = json.loads(render(cc_path, native, home))
    assert cfg["env"]["ANTHROPIC_BASE_URL"] == "https://native.example"
    llm["tools"]["claude-code"]["model"] = "gateway/vendor/model"
    cfg = json.loads(render(cc_path, llm, home))
    assert cfg["env"]["ANTHROPIC_BASE_URL"] == "https://gateway.example"
    assert cfg["model"] == "vendor/model"
    # Switching back removes managed routing left by the selected gateway.
    llm["tools"]["claude-code"]["model"] = "opusplan"
    cfg = json.loads(render(cc_path, llm, home, stdin=json.dumps(cfg)))
    assert "ANTHROPIC_BASE_URL" not in cfg["env"]

print("ok native providers: Aider routing, Goose sync/retry/cleanup, CC deterministic selection")
