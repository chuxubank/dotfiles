# Keep bundled openai and anthropic free for login

Pi stores `/login openai` under the provider id `openai`, and `/login
anthropic` under `anthropic`, both in `auth.json`. A stored credential owns
that provider: it replaces the `apiKey` from `models.json`, while
`models.json`'s `baseUrl` still applies. Reusing those names for the company
proxy sent the subscription token to `llm.invalley.co` and stopped using the
company key.

Pi and OMP now use the names Codex and Hermes already use. `iv-codex` is the
codex token. `iv-cc` is the cc token. Neither alias is bundled, so each
catalog is the enumerated IV list with models-dev metadata. `iv` stays the
default token's OpenAI surface. `iv-anthropic` stays that token's Anthropic
surface for `claude-fable-5`: the cc group 404s that id, and the OpenAI-typed
`iv` alias rejects `reasoning_effort`.

opencode, craft-agents, and claude-code still reuse `openai` / `anthropic`
where that is the tool's own provider key. They do not share Pi's `auth.json`.
