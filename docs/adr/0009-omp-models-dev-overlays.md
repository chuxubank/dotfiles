# Overlay models.dev cards onto exact ids, including subscription prices

SuperGrok and Cursor are personal subscriptions. Their live or bundled catalogs
often ship a bare id, a $0 cost row, or no thinking ladder, so the picker shows
an empty card. Treating those rows as "free because it is a subscription" and
stripping the price would hide the numbers the role table already uses as a
tiebreaker.

`models: false` providers that attach `data_set: models-dev` therefore get the
first-party card on the exact model id: name, thinking, window, list price,
and input modalities. There is no second path that copies only cost for
subscriptions. Effort-suffixed siblings and `model_override_prefixes` still
copy only `cost`, because those keys exist so a rate follows the stem — not
so a first-party name overwrites a live Fast lane. Image `input` is the
exception when the stem has a dedicated `*-fast` key: that lane is the same
model, and Cursor's Grok 4.7 effort ids ship as text-only, so the stem card's
image input is copied onto those siblings. Context-window ids are not effort
suffixes. A stem's `omp_windows` names them, and the same fast-lane patch is
copied onto `{stem}-{window}-fast`. OMP's personal default is the `500k`
window of `${grok_primary}`. Explicit `cost`/`fast` rates on the stem in
`llm.catalogs.cursor` replace the models.dev price, which is how Cursor Fast
stays on the Cursor docs rate rather than the xAI list price. A provider
`model_overrides` entry still wins over that table. Pi reads the same stem
cards and projects cost onto `pi-cursor-sdk` ids (`@window`, `:fast`,
`:slow`). It does not copy names, windows, or thinking ladders onto those ids.
Pi's personal default stays `${grok_primary}@256k:fast`. That id is not the
500k SKU: `pi-cursor-sdk` posts registry id `${grok_primary}` plus `context`,
`reasoning_effort`, and `fast`. `models.list()` still advertises `500k` +
high + fast as the default, and local validation only checks the id, so the
picker shows it. Cursor's run registry then rejects `context=500k` with
`Invalid parameters for registry model` / `AI Model Not Found`.
`context=256k` completes; `context=500k` alone is rejected too, so the
failure is the window, not `reasoning_effort`. Pi still cannot set Grok's
reasoning_effort; the thinking map forwards the default.

Cursor's thinking variants are their own ids (`claude-opus-5-thinking-max`).
Those copies are cost-only too, plus image input when the stem's fast lane
propagates it. A Fast rate still requires an explicit `fast` card; the
standard rate is not reused for it.

One catalog entry per stem holds the rates, Pi windows, and OMP window ids.
These used to be three tables keyed in three grammars (`llm.rates`,
`llm.cursor_pi`, `llm.context_windows`), plus a models.dev provider list and
picker globs copied into each tool. Adding a model meant touching five places
that could drift apart. Tool providers now carry only `catalog: cursor`.

The expansion is blind: it emitted about 2800 OMP overrides, most for ids
Cursor does not serve. The catalog's `ids_cache` holds OMP's own
`omp models cursor` id list; when present, only served ids survive, plus the
`omp_windows` ids OMP synthesizes at request time. Without the cache (CI, a
fresh machine) the full expansion is kept, so a missing list never unprices
a real id.
