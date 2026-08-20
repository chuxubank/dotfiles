# Call lifecycle affiliation owner, not tool

`tool` meant the lifecycle switch, the skill target agent, the service name, the plugin target, and the environment group. Package lookups required a declared name; skill providers and services treated an undeclared name as enabled. That made the same field strict in one resolver and silent in another.

Lifecycle affiliation is now `owner` and must be listed in `tools.yaml`. Services and environment groups keep `tool` as identity and set `owner` only when they should follow a switch. Skill/mcp/plugin `when.*.tool` stays the target agent. Package maps still accept `tool` as an alias so old entries fail closed via `require` rather than silently enabling.
