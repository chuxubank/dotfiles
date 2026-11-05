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
            "api_types": ["openai-completions", "anthropic-messages"],
            "models": ["vendor/model"],
            "auth": {"path": "Test/Gateway", "field": "gateway-key"},
        },
        "second": {"base_url": "https://second.example", "models": ["another/model"]},
        "google": {"type": "google-generative-ai", "models": [], "base_url": "https://google.example"},
        "openrouter": {"base_url": "https://openrouter.example"},
    },
    "tools": {
        "aider": {"model": "gemini/native", "supported_provider_types": ["openai-completions", "anthropic-messages", "google-generative-ai", "ollama"]},
        "goose": {"model": "openrouter/vendor/model", "supported_provider_types": ["openai-completions", "anthropic-messages", "ollama"], "providers": ["openrouter"]},
        "claude-code": {"model": "opusplan", "supported_provider_types": ["anthropic-messages"]},
    },
}


def render(path, llm, home, yaml=False, enabled=True, stdin=None, tools=None):
    source = (root / path).read_text()
    declared = {"goose": {"when": {"enabled": enabled}}}
    declared.update(tools or {})
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
        "tools": declared,
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


def parse_toml(text):
    template = "{{ (" + json.dumps(text) + " | fromToml) | toJson }}"
    result = subprocess.run(command, input=template, text=True, capture_output=True, env={**os.environ, "CI": "true"})
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


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
    template = '{{ includeTemplate "llm/fetch-models" (dict "type" "openai-completions" "base_url" "https://offline.invalid" "auth_key" "" "cache_file" ' + json.dumps(str(model_cache)) + ') }}'
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
    native["providers"]["native"] = {"type": "anthropic-messages", "base_url": "https://native.example"}
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

    # Grok Build selects the upstream model. The alias is the provider.
    # The native Fast pin stays, and the gateway key stays a pass-field command.
    grok_llm = {
        "models": {"grok_primary": "grok-4.7"},
        "default_providers": ["magpie"],
        "providers": {"magpie": {
            "name": "Magpie",
            "base_url": "https://gateway.example",
            "owner": "magpie",
            "api_types": ["openai-completions", "openai-responses", "anthropic-messages", "google-generative-ai"],
            "auth": {"path": "Test/Magpie", "field": "gateway-key"},
        }},
        "tools": {"grok": {
            "supported_provider_types": ["openai-completions", "openai-responses"],
            "model": [
                "magpie/grok/${grok_primary}-build-fast@500k",
                "${grok_primary}-build-fast",
            ],
        }},
    }
    grok_path = "home/dot_grok/modify_config.toml"
    prior = """
[models]
default = "magpie"

[endpoints]
models_base_url = "https://old.example/v1"

[auth]
auth_provider_command = "old"

[model.magpie]
model = "old"
api_key = "secret"

[model."grok/grok-4.7-build-fast@500k"]
model_provider = "magpie"
api_key = "secret"

[model."grok-4.7-build-fast"]
context_window = 1
temperature = 0.2

[model.custom]
temperature = 0.1

[model_providers.magpie]
base_url = "https://old.example/v1"

[auth_provider.magpie]
command = "old"
"""
    on = parse_toml(render(
        grok_path, grok_llm, home, stdin=prior,
        tools={"magpie": {"when": {"enabled": True}}},
    ))
    grok_id = "grok/grok-4.7-build-fast@500k"
    assert on["models"]["default"] == grok_id
    assert on["endpoints"]["models_base_url"] == "https://gateway.example/v1"
    helper = on["auth"]["auth_provider_command"]
    assert helper == f"'{home / 'bin' / 'pass-field'}' 'Test/Magpie' 'gateway-key'", helper
    assert "magpie" not in on["model"] and grok_id not in on["model"]
    assert "model_providers" not in on or "magpie" not in on["model_providers"]
    assert "auth_provider" not in on or "magpie" not in on["auth_provider"]
    assert on["model"]["grok-4.7-build-fast"]["context_window"] == 500000
    assert on["model"]["grok-4.7-build-fast"]["temperature"] == 0.2
    assert on["model"]["custom"]["temperature"] == 0.1
    off = parse_toml(render(
        grok_path, grok_llm, home, stdin=prior,
        tools={"magpie": {"when": {"enabled": False}}},
    ))
    assert off["models"]["default"] == "grok-4.7-build-fast"
    assert "endpoints" not in off or "models_base_url" not in off["endpoints"]
    assert "auth" not in off or "auth_provider_command" not in off["auth"]
    assert "magpie" not in off["model"] and grok_id not in off["model"]
    assert "model_providers" not in off or "magpie" not in off["model_providers"]
    assert "auth_provider" not in off or "magpie" not in off["auth_provider"]
    assert off["model"]["custom"]["temperature"] == 0.1

    # The winning alias is the one models endpoint. A later alias does not
    # get a second catalog entry.
    routed = copy.deepcopy(grok_llm)
    routed["default_providers"] = ["gateway", "magpie"]
    routed["providers"]["gateway"] = {
        "name": "Gateway",
        "base_url": "https://other.example",
        "api_types": ["openai-completions"],
        "auth": {"path": "Test/Gateway", "field": "gateway-key"},
    }
    routed["tools"]["grok"]["model"] = [
        "gateway/vendor/model",
        "magpie/grok/${grok_primary}-build-fast@500k",
        "${grok_primary}-build-fast",
    ]
    chosen = parse_toml(render(
        grok_path, routed, home, stdin=prior,
        tools={"magpie": {"when": {"enabled": True}}},
    ))
    assert chosen["models"]["default"] == "vendor/model"
    assert chosen["endpoints"]["models_base_url"] == "https://other.example/v1"
    helper = chosen["auth"]["auth_provider_command"]
    assert helper == f"'{home / 'bin' / 'pass-field'}' 'Test/Gateway' 'gateway-key'", helper
    assert "vendor/model" not in chosen["model"]
    assert grok_id not in chosen["model"] and "magpie" not in chosen["model"]
    assert "model_providers" not in chosen or not chosen["model_providers"]
    assert "magpie" not in chosen.get("auth_provider", {})
    assert chosen["model"]["custom"]["temperature"] == 0.1
    pooled = copy.deepcopy(routed)
    pooled["providers"]["magpie"]["enabled_models"] = ["**"]
    pooled["tools"]["grok"]["enabled_models"] = ["${grok_primary}-build-fast*"]
    both = parse_toml(render(
        grok_path, pooled, home, stdin=prior,
        tools={"magpie": {"when": {"enabled": True}}},
    ))
    assert both["models"]["default"] == "vendor/model"
    assert both["endpoints"]["models_base_url"] == "https://other.example/v1"
    assert grok_id not in both["model"] and "magpie" not in both["model"]
    assert "model_providers" not in both or "magpie" not in both["model_providers"]
    assert both["model"]["grok-4.7-build-fast"]["context_window"] == 500000

    # Craft takes the protocol path from the provider type. The alias name
    # does not decide whether /v1 is appended.
    craft_llm = {
        "models": {},
        "default_providers": ["gateway", "router", "local", "claude", "gemini", "versioned"],
        "providers": {
            "gateway": {"base_url": "https://gateway.example", "models": False},
            "router": {"base_url": "https://openrouter.ai/api", "models": False},
            "local": {"type": "ollama", "base_url": "http://localhost:11434", "models": False},
            "claude": {"type": "anthropic-messages", "base_url": "https://anthropic.example", "models": False},
            "gemini": {"type": "google-generative-ai", "base_url": "https://generativelanguage.googleapis.com", "models": False},
            "versioned": {"base_url": "https://integrate.api.nvidia.com/v1", "models": False},
        },
        "tools": {"craft-agents": {"model": "gateway/vendor/model"}},
    }
    craft = json.loads(render("home/dot_craft-agent/config.json.tmpl", craft_llm, home))
    bases = {item["slug"]: item.get("baseUrl") for item in craft["llmConnections"]}
    assert bases == {
        "gateway": "https://gateway.example/v1",
        "router": "https://openrouter.ai/api/v1",
        "local": "http://localhost:11434/v1",
        "claude": "https://anthropic.example",
        "gemini": "https://generativelanguage.googleapis.com/v1beta",
        "versioned": "https://integrate.api.nvidia.com/v1",
    }, bases
    assert craft["defaultLlmConnection"] == "gateway"
    winner = next(item for item in craft["llmConnections"] if item["slug"] == "gateway")
    assert winner["defaultModel"] == "vendor/model", winner

print("ok native providers: Aider routing, Goose sync/retry/cleanup, CC deterministic selection, Grok provider pool, Craft endpoints")
