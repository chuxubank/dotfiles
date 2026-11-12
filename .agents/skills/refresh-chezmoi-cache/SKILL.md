---
name: refresh-chezmoi-cache
description: >
  Drop one chezmoi cache entry so the next apply refetches that target.
  Use when a GitHub template function, external download, git-repo pull, or
  modify-directory command is still serving a cached result, or when the
  user asks to clear that cache and apply one target. --refresh-externals
  refetches every external in the apply; use the one-entry delete unless
  the user asked for all of them.
---

# Refresh one chezmoi cache entry

A cached result stays in use until its period elapses or that one entry is
removed. Delete the entry that holds the stale result, then apply the one
target. Leave every other key in place.

GitHub template functions share `[gitHub] refreshPeriod` in
`home/.chezmoi.toml.tmpl`, measured from `requestedAt`. An external,
git-repo, or modify-directory command uses the `refreshPeriod` on its own
entry. Omitted, that period is 0: the cached result stays until this entry
is removed.

Run the delete and apply only after the user asks to install or refresh
that target.

## Refresh the target

1. Find the source entry and the one cache that holds its stale result.
   The external key is relative to the directory that holds the
   `.chezmoiexternal` file. `home/` is the destination home, and a key in
   `home/.chezmoiexternals/` is already relative to home. Stop when the
   surrounding condition does not render the entry on this host. Done when
   you have one absolute target and one cache entry from the table below.

2. Read that entry and compare it with the version the user named, or with
   upstream when they did not name one.

   ```sh
   chezmoi state get --bucket=<bucket> --key=<key>
   ```

   Done when you know whether the cached value is the one apply would use.
   When it is already that value, leave the entry. Apply the target only if
   the installed file is still older. When the installed file already
   matches, report that and stop.

3. Remove that one entry, then apply that target:

   ```sh
   chezmoi state delete --bucket=<bucket> --key=<key>
   chezmoi apply --no-tty <absolute-target>
   ```

   A download is a file, not a state key: remove
   `<cache>/external/<sha256>` and then apply. Read the cache directory
   from `chezmoi doctor`. The hash is the hex SHA-256 of the exact URL
   string. Apply that target. `make apply` and `./install.sh` install the
   machine. `--refresh-externals` refetches every external read by that
   apply; use it only when the user asked to refresh all of them. Done
   when apply exits 0, the cache entry shows the new result, and the
   target's own version check matches it. On a template or download error,
   stop and report it.

4. Tell the user the file is updated. A process that already loaded a
   binary keeps the previous one until that process is restarted. Restart
   it only when the user asks.

## Which entry

| What is stale | Bucket or file | Key |
| --- | --- | --- |
| `gitHubLatestRelease`, `gitHubLatestReleaseAssetURL` | `gitHubLatestReleaseState` | `owner/repo` |
| `gitHubRelease`, `gitHubReleaseAssetURL` | `gitHubVersionReleaseState` | `owner/repo/<version>` |
| `gitHubReleases` | `gitHubReleasesState` | `owner/repo` |
| `gitHubTags`, `gitHubLatestTag` | `gitHubTagsState` | `owner/repo` |
| `gitHubKeys` | the keys bucket `chezmoi state dump` lists | GitHub user |
| file or archive external whose URL string changes | none, after the template cache above is current | a new URL is a new download file |
| file or archive external whose URL string stays the same, including `.../latest/...` | `<cache>/external/<sha256 of that URL>` | that URL |
| `git-repo` external, or a modify-directory command | `gitRepoExternalState` | absolute target path |

`gitHubKeys` has been stored as `gitHubKeysState` and as
`gitHubLatestKeysState`. Use the bucket present in `chezmoi state dump`.

A versioned asset URL changes only after its GitHub entry misses. Remove
the download file only when the URL string itself stays the same.

`entryState` and `configState` record what was applied. They are not
upstream caches. `scriptState` records `run_once` scripts by the hex
SHA-256 of the script contents, with the script name in `name`. Delete
that one key, then apply, only when the user asks to run that script again.
