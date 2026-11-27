#!/usr/bin/env python3
"""Offline checks for shared provider defaults, precedence, exclusions and policy."""

import copy
import json
import sys
from pathlib import Path

from _testlib import capture, context_overlay

root = Path(sys.argv[1]).resolve()
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
    template = (
        context_overlay({"llm": llm}, clear=("llm",))
        + '{{- includeTemplate "llm/tool-config" (mergeOverwrite $ctx (dict "tool" '
        + json.dumps(tool) + ")) -}}"
    )
    result = capture(root, ["execute-template"], stdin=template)
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

# Floors are opt-in. A family glob loses its own digits; * / ** become those
# families only; a pattern that names no floor is unchanged. Disabled aliases
# still contribute nothing, so this fixture's gateway/* does expand.
gpt = "gpt-{6.[2-9]*,6.[1-9][0-9]*,[7-9]*,[1-9][0-9]*}"
opus = "claude-opus-{5,5[!0-9.-]*,5.*,5-*,[6-9]*,[1-9][0-9]*}"
data = copy.deepcopy(fixture)
data["model_floors"] = [
    {"stem": "gpt-", "min": "6.2"},
    {"stem": "claude-opus-", "min": "5", "seps": [".", "-"]},
]
data["default_providers"] = ["gateway"]
data["tools"]["fixture"]["enabled_models"] = ["gpt-*", "composer-2.5*", "gateway/claude-opus-*"]
assert render(data)["enabled_models"] == [
    "**/" + gpt,
    "composer-2.5*",
    "gateway/**/" + opus,
    "gateway/**/{%s,%s}" % (gpt, opus),
]
data["model_floors"] = [{"stem": "gpt-", "min": "6.21"}]
render(data, error="model floor")

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

# A ref plugin follows plugins/resolve for this tool. Off, the alias is
# absent, so its picker globs and model candidates drop. An unknown name fails.
def render_plugins(llm, providers, error=None):
    template = (
        context_overlay({"llm": llm, "plugins": {"fixture": {"providers": providers}}}, clear=("llm",))
        + '{{- includeTemplate "llm/tool-config" (mergeOverwrite $ctx (dict "tool" "fixture")) -}}'
    )
    result = capture(root, ["execute-template"], stdin=template)
    if error:
        assert result.returncode != 0 and error in result.stderr, result.stderr
        return None
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


plugin = {"name": "pi-cursor-sdk", "source": "npm:pi-cursor-sdk"}
plugin_data = copy.deepcopy(fixture)
plugin_data["default_providers"] = ["other"]
plugin_data["tools"]["fixture"] = {
    "providers": {"cursor": {"provider": "gateway", "plugin": "pi-cursor-sdk"}},
    "enabled_models": ["cursor/kept", "other/*"],
    "model": ["cursor/model", "other/model"],
}
off = render_plugins(plugin_data, [{**plugin, "when": {"enabled": False}}])
assert "cursor" not in off["providers"]
assert off["enabled_models"] == ["other/*"]
assert off["model"] == "other/model"
on = render_plugins(plugin_data, [{**plugin, "when": {"enabled": True}}])
assert "cursor" in on["providers"]
assert on["enabled_models"] == ["cursor/kept", "other/*", "cursor/*"]
assert on["model"] == "cursor/model"
plugin_data["tools"]["fixture"]["providers"]["cursor"]["plugin"] = "not-a-plugin"
render_plugins(plugin_data, [{**plugin, "when": {"enabled": True}}], error='unknown plugin "not-a-plugin"')

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
data["providers"]["gateway"]["api_types"] = ["openai-completions", "openai-responses", "anthropic-messages", "google-generative-ai"]
data["tools"]["fixture"] = {
    "supported_provider_types": ["anthropic-messages"],
    "enabled_models": ["other/*"],
}
result = render(data)
assert set(result["providers"]) == {"gateway"}
assert result["providers"]["gateway"]["type"] == "anthropic-messages"
assert result["enabled_models"] == ["gateway/*"]
# The first api_types entry is the primary when the client accepts it.
data["providers"]["gateway"]["api_types"] = ["anthropic-messages", "openai-completions"]
data["tools"]["fixture"]["supported_provider_types"] = ["openai-completions", "anthropic-messages"]
assert render(data)["providers"]["gateway"]["type"] == "anthropic-messages"
data["tools"]["fixture"]["providers"] = {"gateway": {"type": "openai-completions"}}
data["tools"]["fixture"]["supported_provider_types"] = ["anthropic-messages"]
assert render(data)["providers"] == {}

# Shared sets use the same precedence as explicit sets, with tool refs last.
data = copy.deepcopy(fixture)
data["default_provider_sets"] = ["shared"]
data["provider_sets"] = {"shared": {"alias": {"provider": "gateway", "headers": {"winner": "default"}}}}
data["tools"]["fixture"] = {"providers": {"alias": {"headers": {"winner": "tool"}}}}
assert render(data)["providers"]["alias"]["headers"] == {"winner": "tool"}
data["tools"]["fixture"]["exclude_providers"] = ["alias"]
assert render(data)["providers"] == {}
data["default_provider_sets"] = ["missing"]
render(data, error='unknown set "missing"')

# Exercise the repository declarations, not a duplicate opt-in table. No
# credentials/catalogs are fetched: CI suppresses pass, and only routing
# fields from tool-config are returned.
for host in ("iv", "personal", "ci"):
    template = r'''
{{- $ctx := mergeOverwrite (deepCopy .) (dict "host_env" HOST) -}}
{{- $result := dict -}}
{{- range $tool, $_ := $ctx.llm.tools -}}
  {{- $cfg := includeTemplate "llm/tool-config" (mergeOverwrite (deepCopy $ctx) (dict "tool" $tool)) | fromJson -}}
  {{- $iv := dict -}}
  {{- range $alias := list "iv-codex" "iv-cc" "iv-anthropic" "iv" -}}
    {{- if hasKey $cfg.providers $alias -}}
      {{- $_ := set $iv $alias (pick (index $cfg.providers $alias) "type" "auth_field") -}}
    {{- end -}}
  {{- end -}}
  {{- $_ := set $result $tool (dict "providers" $iv "patterns" (default (list) (index $cfg "enabled_models")) "model_provider" (default "" (index $cfg "model_provider"))) -}}
{{- end -}}
{{- $result | toJson -}}
'''.replace("HOST", json.dumps(host))
    result = capture(root, ["execute-template"], stdin=template, env={"CI": "true"})
    assert result.returncode == 0, result.stderr
    for tool, cfg in json.loads(result.stdout).items():
        aliases = set(cfg["providers"])
        if tool == "pen" and host != "ci":
            assert cfg["model_provider"] == ("iv-codex" if host == "iv" else "magpie"), (host, cfg)
        if host != "iv":
            assert not aliases, (host, tool, cfg)
            assert not any(p.startswith(("iv/", "iv-codex/", "iv-cc/", "iv-anthropic/")) for p in cfg["patterns"])
            continue
        expected = {"iv", "iv-codex", "iv-cc", "iv-anthropic"}
        if tool == "codex":
            expected.remove("iv-anthropic")
        elif tool == "claude-code":
            expected = {"iv-cc", "iv-anthropic"}
        assert aliases == expected, (tool, cfg)
        for alias, provider in cfg["providers"].items():
            field = {"iv": "default-auth-token", "iv-anthropic": "default-auth-token", "iv-codex": "codex-auth-token", "iv-cc": "cc-auth-token"}[alias]
            assert provider["auth_field"] == field, (tool, alias, provider)
        if tool == "pen":
            assert cfg["providers"]["iv"]["type"] == "openai-completions"
            assert cfg["providers"]["iv-codex"]["type"] == "openai-completions"
            assert cfg["providers"]["iv-cc"]["type"] == "anthropic-messages"
            assert cfg["providers"]["iv-anthropic"]["type"] == "anthropic-messages"
        if tool in ("pi", "omp"):
            gpt = "gpt-{6,6[!0-9.]*,6.*,[7-9]*,[1-9][0-9]*}"
            assert any(gpt in p for p in cfg["patterns"]), (tool, cfg["patterns"])
            assert not any(p in {"*", "**", alias + "/*", alias + "/**"} for alias in (*expected, "magpie") for p in cfg["patterns"]), (tool, cfg["patterns"])

print("ok LLM providers: defaults, precedence, exclusions, protocol negotiation, IV client/host matrix and picker policy")
