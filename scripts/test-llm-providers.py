#!/usr/bin/env python3
"""Offline checks for shared provider defaults, precedence, exclusions and policy."""

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
command = ["chezmoi"]
for flag, key in (("--persistent-state", "CHEZMOI_VERIFY_STATE"), ("--cache", "CHEZMOI_VERIFY_CACHE")):
    if os.environ.get(key):
        command.extend([flag, os.environ[key]])
command.extend(["execute-template", "--source", str(root)])
fixture = {
    "models": {},
    "providers": {
        "gateway": {"base_url": "https://gateway.example", "enabled_models": ["*"]},
        "other": {"base_url": "https://other.example"},
        "off": {"when": {"enabled": False}},
        "openrouter": {},
    },
    "tools": {"fixture": {}},
}


def render(llm, tool="fixture", error=None):
    payload = json.dumps(json.dumps(llm))
    template = (
        '{{- $ctx := deepCopy . -}}{{- $_ := set $ctx "llm" (' + payload + ' | fromJson) -}}'
        '{{- includeTemplate "llm/tool-config" (mergeOverwrite $ctx (dict "tool" '
        + json.dumps(tool) + ")) -}}"
    )
    result = subprocess.run(command, input=template, text=True, capture_output=True)
    if error:
        assert result.returncode != 0 and error in result.stderr, result.stderr
        return None
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


# Missing and empty defaults preserve opt-in behavior.
for defaults in (None, [], {}):
    data = copy.deepcopy(fixture)
    if defaults is not None:
        data["default_providers"] = defaults
    assert render(data)["providers"] == {}

# Both reference forms work without any per-tool declaration.
for defaults in (["gateway"], {"gateway": {"provider": "gateway"}}):
    data = copy.deepcopy(fixture)
    data["default_providers"] = defaults
    data["tools"]["fixture"]["enabled_models"] = ["first"]
    result = render(data)
    assert set(result["providers"]) == {"gateway"}
    assert result["enabled_models"] == ["first", "gateway/*"]

# Defaults < ordered sets < tool, preserving nested fields and explicit false.
data = copy.deepcopy(fixture)
data["default_providers"] = {
    "shared": {"provider": "gateway", "headers": {"default": "kept", "winner": "default"}},
    "off": {"provider": "off"},
}
data["provider_sets"] = {
    "first": {"shared": {"name": "From set", "headers": {"winner": "first"}}},
    "second": {"shared": {"headers": {"winner": "second", "second": "kept"}}},
}
data["tools"]["fixture"] = {
    "provider_sets": ["first", "second"],
    "providers": {"shared": {"models": False, "headers": {"winner": "tool"}}},
}
result = render(data)
shared = result["providers"]["shared"]
assert shared["name"] == "gateway" and shared["display_name"] == "From set"
assert shared["models"] is False
assert shared["headers"] == {"default": "kept", "second": "kept", "winner": "tool"}
assert "off" not in result["providers"]

# Short tool refs also preserve inherited settings; map refs may remap an alias.
data["tools"]["fixture"]["providers"] = ["shared"]
data["providers"]["shared"] = {"base_url": "https://short.example"}
assert render(data)["providers"]["shared"]["headers"]["winner"] == "second"
data["tools"]["fixture"]["providers"] = {"shared": {"provider": "other"}}
assert render(data)["providers"]["shared"]["base_url"] == "https://other.example"

# Exclusions win over defaults, sets and explicit tool refs. They also remove
# picker patterns and cause model/role candidate lists to take the fallback.
data["tools"]["fixture"].update({
    "exclude_providers": ["shared", "missing"],
    "providers": {"shared": {"provider": "gateway"}, "other": {"provider": "other"}},
    "enabled_models": ["shared/*", "off/*", "other/*"],
    "model": ["shared/model", "other/model"],
    "default_models": {"task": ["shared/model", "other/model"]},
})
result = render(data)
assert set(result["providers"]) == {"other"}
assert result["enabled_models"] == ["other/*"]
assert result["model"] == "other/model" and result["default_models"]["task"] == "other/model"

# Invalid effective refs fail early, including inherited OpenRouter aliases.
data = copy.deepcopy(fixture)
data["default_providers"] = ["missing"]
render(data, error='unknown provider "missing"')
data = copy.deepcopy(fixture)
data["tools"]["fixture"]["provider_sets"] = ["missing"]
render(data, error='unknown set "missing"')
for tool in ("pi", "omp", "hermes", "opencode"):
    for ref in ({"openrouter": {"provider": "other"}}, {"router": {"provider": "openrouter"}}):
        for source in ("default", "set"):
            data = copy.deepcopy(fixture)
            data["tools"] = {tool: {}}
            if source == "default":
                data["default_providers"] = ref
            else:
                data["provider_sets"] = {"fixture": ref}
                data["tools"][tool]["provider_sets"] = ["fixture"]
            render(data, tool=tool, error="OpenRouter provider is not allowed")
            data["tools"][tool]["exclude_providers"] = list(ref)
            assert render(data, tool=tool)["providers"] == {}

# Protocol filtering is by capability, not a hard-coded provider blacklist.
# A multi-protocol gateway adapts to CC; an explicit incompatible override
# is filtered, never silently rewritten to a different protocol.
data = copy.deepcopy(fixture)
data["default_providers"] = ["gateway", "other"]
data["providers"]["gateway"]["api_types"] = ["openai", "anthropic", "gemini"]
data["tools"]["fixture"] = {
    "supported_provider_types": ["anthropic"],
    "enabled_models": ["other/*"],
}
result = render(data)
assert set(result["providers"]) == {"gateway"}
assert result["providers"]["gateway"]["type"] == "anthropic"
assert result["enabled_models"] == ["gateway/*"]
data["tools"]["fixture"]["providers"] = {"gateway": {"type": "openai"}}
assert render(data)["providers"] == {}

# Pi's real candidate list prefers Magpie only while its alias resolves.
# Stub endpoints/auth/catalogs so neither credentials nor the gateway is used.
pi_config = subprocess.run(
    command, input="{{ .llm.tools.pi | toJson }}", text=True, capture_output=True,
)
assert pi_config.returncode == 0, pi_config.stderr
pi_models = json.loads(pi_config.stdout)["model"]
assert pi_models[0] == "magpie/auto-grok-4.7@500k"
for magpie_on in (True, False):
    for iv_on in (True, False):
        data = {
            "models": {"gpt_primary": "gpt-fixture", "grok_primary": "grok-fixture"},
            "default_providers": ["magpie"],
            "providers": {
                "magpie": {"when": {"enabled": magpie_on}, "enabled_models": ["**"]},
                "iv-codex": {"when": {"enabled": iv_on}},
                "iv-cc": {"when": {"enabled": iv_on}},
                "xai": {},
                "cursor": {},
                "openai-codex": {"when": {"enabled": False}},
            },
            "tools": {"pi": {
                "model": pi_models,
                "enabled_models": [],
                "providers": ["iv-codex", "iv-cc", "xai", "cursor", "openai-codex"],
            }},
        }
        result = render(data, tool="pi")
        expected = (
            "magpie/auto-grok-4.7@500k" if magpie_on
            else "iv-codex/gpt-fixture" if iv_on else "xai/grok-fixture"
        )
        assert result["model"] == expected, result
        provider, model_id = expected.split("/", 1)
        assert result["model_provider"] == provider and result["model_id"] == model_id
        assert ("magpie/**" in result["enabled_models"]) == magpie_on

print("ok LLM providers: defaults, precedence, exclusions, protocol negotiation, gates and policy")
