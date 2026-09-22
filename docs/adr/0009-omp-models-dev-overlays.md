# Overlay models.dev cards onto exact ids, including subscription prices

SuperGrok and Cursor are personal subscriptions. Their live or bundled catalogs
often ship a bare id, a $0 cost row, or no thinking ladder, so the picker shows
an empty card. Treating those rows as "free because it is a subscription" and
stripping the price would hide the numbers the role table already uses as a
tiebreaker.

`models: false` providers that attach `data_set: models-dev` therefore get the
first-party card on the exact model id: name, thinking, window, and list price.
There is no second path that copies only cost for subscriptions. Effort-suffixed
siblings and `model_override_prefixes` still copy only `cost`, because those
keys exist so a rate follows the stem — not so a first-party name overwrites a
live Fast lane. An explicit `model_overrides` entry still wins, which is how
Cursor Fast stays on the Cursor docs rate rather than the xAI list price.
