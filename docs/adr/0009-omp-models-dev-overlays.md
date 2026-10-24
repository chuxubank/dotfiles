# Overlay models.dev cards onto exact ids, including subscription prices

SuperGrok is a personal subscription. Its live catalog often ships a bare
id, a $0 cost row, or no thinking ladder, so the picker shows
an empty card. Treating those rows as "free because it is a subscription" and
stripping the price would hide the numbers the role table already uses as a
tiebreaker.

`models: false` providers that attach `data_set: models-dev` therefore get the
first-party card on the exact model id: name, thinking, window, list price,
and input modalities. There is no second path that copies only cost for
subscriptions. Effort-suffixed siblings and `model_override_prefixes` still
copy only `cost`, because those keys exist so a rate follows the stem — not
so a first-party name overwrites a live Fast lane.

Cursor is the exception. OMP's bundled Cursor catalog plus live discovery
already price every served id, Fast lanes and context SKUs included
(`grok-4.7-500k-fast` is 500k at the Fast rate with `extendedContext` on).
The models.dev overlay replaced Cursor's windows and long-context tiers with
the vendor API's (1.05M instead of Cursor's 272k for GPT-5.6, a 200k Grok
tier instead of 256k) and invented about 2800 ids Cursor does not serve, so
OMP's Cursor provider now gets none.

Pi still needs prices: `pi-cursor-sdk` discovers every model at $0.
`llm.catalogs.cursor` holds one entry per stem — standard `cost`, `fast`,
`pi_contexts`, `pi_default_fast` — with the standard rate falling back to
the models.dev card. Pi projects cost onto `pi-cursor-sdk` ids (`@window`, `:fast`,
`:slow`). It does not copy names, windows, or thinking ladders onto those ids.
Pi's Cursor grok candidate is `${grok_primary}@500k:fast`, the same 500k Fast
grok as OMP's `${grok_primary}-500k-fast` and Grok Build's
`${grok_primary}-build-fast` at a 500k window. The session default is the `xai` candidate listed ahead of it. The Cursor id is still not the OMP
SKU: `pi-cursor-sdk` posts registry id `${grok_primary}` plus `context`,
`reasoning_effort`, and `fast`. `models.list()` advertises `500k` + high +
fast as the default variant, and local validation only checks the id. A probe
on 2026-10-02 had the run registry reject `context=500k` with
`Invalid parameters for registry model` / `AI Model Not Found`, and
`context=256k` completed, so the pin sat at `@256k:fast`. The pin is 500k
again so Grok, Pi, and OMP share one grok. Pi still cannot set Grok's
reasoning_effort; the thinking map forwards the default.

Fast rates come only from an explicit `fast` card; the standard rate is not
reused for them. These fields used to be three tables keyed in three
grammars plus per-tool copies of the provider list and picker globs; the
picker globs now live once on `llm.providers.cursor.enabled_models`.
