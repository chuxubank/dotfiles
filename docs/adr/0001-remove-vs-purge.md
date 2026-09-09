# Split dest cleanup into remove and purge

Turning a tool off used to list `/**` directory wipes in `remove`, so cleanup deleted login state, history, and caches together with managed config. The alternative was to stop deleting dest files entirely and rely on ignore, which would leave stale managed files in place.

`remove` is now the managed-file list and always runs when the tool is off. `purge` holds runtime data and runs only when `policies.purge_disabled_tools` is on. The policy is explicit rather than implied by disabling a tool; this repository currently enables it, so disabled-tool runtime data is moved to Trash during apply.

`.chezmoiremove` remains responsible for files and symlinks. With chezmoi v2.72.1, listing an empty or non-empty directory, including through `dir/**`, fails with `Expected a file, got a directory`; targets also matched by `.chezmoiignore` are never removed. Disabled-tool trees are intentionally ignored, so `run_after_020_purge-disabled-tools.sh.tmpl` must reconcile directory purges on every apply.
