# Tier OMP model roles by host through candidate lists

OMP resolves nine named model roles, and the models worth assigning to them
differ by host: IV is company-funded, while SuperGrok, ChatGPT, and Cursor are
personal subscriptions. Writing one model per role picks a single tier for every
host, and the earlier table did exactly that — `smol`, `task`, and `advisor` all
named `xai-oauth/grok-4.6`, so the IV machine spent a personal subscription on
company work. The obvious fix is a host conditional in
`modify_config.yml`, which would put a second host-env table in the template and
split the decision across two files.

Roles instead take candidate lists, and `llm/pick-model` selects the first entry
whose provider alias resolved on this host. The IV aliases already carry
`when.enabled.host_env: [iv]`, so listing an IV entry first and a subscription
entry second expresses both tiers in one place with no conditional: on `iv` the
IV entry wins, elsewhere it fails to resolve and the fallback takes over. This
reuses the mechanism `model` and `slow` already used rather than adding one, and
it keeps the per-role tier choice next to the role.

The consequence is that a role's effective model is not readable from the data
file alone — it depends on which aliases resolved. `docs/llm/model-roles.md`
carries the resolved table for both tiers, and both must move together.
Verifying the non-IV tier needs an explicit render
(`chezmoi execute-template` with `host_env` overridden), because the working host
only ever exercises one branch.

Effort is part of the tier, not a global. The IV entries spend it freely and the
fallback entries stay lower, so the same role can be `:high` on IV and
`:medium` on a personal host. Because effort levels are per-model, a fallback
cannot assume the level its IV sibling uses: `gpt-5.6-luna` has no `minimal`
while `grok-4.6` does.

Leaving a role unset is a real option and is preferred over an assignment that
duplicates the fallback OMP would pick anyway. `vision` unset resolves through
`@default`, which already advertises image input on both tiers; assigning it
would only add a model to maintain. An explicit assignment earns its place by
changing the model, or by changing the effort — which is the sole reason `tiny`
exists next to `smol` on the IV tier.

Where the catalog presents two models as equivalent, price is the tiebreaker and
it is not visible in the model name. `gpt-5.6-sol` and `gpt-5.6-terra` match on
context, max output, and effort levels and share a $1.5 input rate, but output is
$12 against $2. So the pairing follows output volume rather than prestige: the
role that emits the most tokens, `task`, takes the cheap-output model, and the
role that runs least often, `plan`, is where an expensive model is affordable.
Read the cost fields before assigning a role; sibling models are not
interchangeable just because their capability rows are identical.
