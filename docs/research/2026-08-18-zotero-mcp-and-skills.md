# Zotero MCP servers and agent skills — market survey

**Date:** 2026-08-18  
**Goal:** pick one MCP server (and optionally one skill) for a personal chezmoi-managed agent setup (Cursor, Claude Code, Codex, OpenCode, Goose, etc.).  
**Method:** GitHub API, official Zotero docs, PyPI/npm package metadata, official MCP registry, skills.sh CLI, Smithery/Glama/mcp.so listings. Every numeric claim below was read from the owning source on this date. Do not treat secondary blogs as authoritative.

**Critical naming collision:** `uvx zotero-mcp` installs **kujenga/zotero-mcp** ([PyPI `zotero-mcp` 0.3.1](https://pypi.org/project/zotero-mcp/)). The popular full-featured server is **`zotero-mcp-server`** from [54yyyu/zotero-mcp](https://github.com/54yyyu/zotero-mcp) ([PyPI `zotero-mcp-server` 0.9.1](https://pypi.org/project/zotero-mcp-server/)). Installing the wrong package is the most common setup mistake.

**`stevennevins/zotero-mcp` does not exist.** GitHub search for `zotero-mcp user:stevennevins` returned 0 repos. [stevennevins](https://github.com/stevennevins) publishes other MCP servers (`architect-mcp-server`, `mcp-server-template`) but not a Zotero one. The likely mix-up is [54yyyu/zotero-mcp](https://github.com/54yyyu/zotero-mcp), whose docs live at [stevenyuyy.com/zotero-mcp](https://stevenyuyy.com/zotero-mcp/). The other frequently cited name is [kaliaboi/mcp-zotero](https://github.com/kaliaboi/mcp-zotero) (note: `mcp-zotero`, not `zotero-mcp`).

---

## 1. Recommendation

**Use [54yyyu/zotero-mcp](https://github.com/54yyyu/zotero-mcp) via the PyPI package `zotero-mcp-server`.** Optionally add a thin local skill that teaches agents to prefer `zotero-cli` for shell-capable hosts. Do not install a marketplace Zotero skill as the primary integration.

### Why this MCP

| Criterion | Evidence |
|---|---|
| Popularity | **4,691 stars**, 379 forks, 59 open issues ([GitHub API, 2026-08-17](https://api.github.com/repos/54yyyu/zotero-mcp)) |
| Maintenance | Last commit **2026-08-13** (`f331646`, “Merge pull request #444…”) |
| Package | [`zotero-mcp-server` 0.9.1](https://pypi.org/project/zotero-mcp-server/) uploaded **2026-08-06**; Python ≥3.10; MIT |
| Registry | Listed as `io.github.54yyyu/zotero-mcp` versions 0.6.4–0.9.1 on the [official MCP registry](https://registry.modelcontextprotocol.io/v0.1/servers?search=zotero) |
| Transport | stdio (default), plus `streamable-http` / `sse` ([README](https://github.com/54yyyu/zotero-mcp/blob/main/README.md)) — works in Cursor, Claude Code, Codex, OpenCode, Goose |
| Zotero access | Local API (port 23119), Web API, or hybrid (local reads + web writes) ([README](https://github.com/54yyyu/zotero-mcp/blob/main/README.md)) |
| Agent-friendly extras | `zotero-cli` for shell agents; `ZOTERO_MCP_TOOLSETS` to keep tool schemas off the context window ([README](https://github.com/54yyyu/zotero-mcp/blob/main/README.md)) |
| No extra Zotero plugin | Local API is built into Zotero 7+ ([official Local API docs](https://www.zotero.org/support/dev/web_api/v3/local_api)) |

Runner-up if you want **three tools and nothing else:** [kujenga/zotero-mcp](https://github.com/kujenga/zotero-mcp) (161 stars, last commit 2026-08-07, PyPI name `zotero-mcp`, official registry `io.github.kujenga/zotero-mcp`).

Runner-up if you want **in-process Zotero JS writes without a zotero.org key:** [cookjohn/zotero-mcp](https://github.com/cookjohn/zotero-mcp) (1,083 stars). It is a Zotero plugin that hosts Streamable HTTP on **port 23120**, last release 2026-06-11. Worse fit for a multi-agent chezmoi setup because every client must speak Streamable HTTP and Zotero must be running.

### Why not a marketplace skill as the primary layer

Skills on skills.sh either (a) wrap pyzotero / curl and duplicate what MCP already does, (b) wrap 54yyyu with Logseq-specific output, or (c) execute code / read `zotero.sqlite` directly. For Cursor + Claude Code + Codex + OpenCode + Goose, one stdio MCP plus the bundled `zotero-cli` covers all hosts. If you want a skill, write a 30-line local `SKILL.md` that points at those two entry points (see §6).

---

## 2. MCP comparison table

Stars, last commit, and license are from the GitHub API on 2026-08-17/18. Package versions are from PyPI/npm JSON on 2026-08-18.

| Project | Stars | Last commit | Lang | Install | Talks to Zotero via | Tools (owner-stated) | Auth / setup | License | Health |
|---|---:|---|---|---|---|---|---|---|---|
| [54yyyu/zotero-mcp](https://github.com/54yyyu/zotero-mcp) | 4691 | 2026-08-13 | Python | `uv tool install zotero-mcp-server`; Docker `ghcr.io/54yyyu/zotero-mcp` | Local API, Web API, hybrid; optional ChromaDB index of `zotero.sqlite` for semantic search | Search, metadata, fulltext, annotations, notes, add-by-DOI/URL/ISBN/BibTeX, collections, tags, optional scite/duplicates/relations ([README tool list](https://github.com/54yyyu/zotero-mcp/blob/main/README.md)) | Local: `ZOTERO_LOCAL=true`. Writes: `ZOTERO_API_KEY` + `ZOTERO_LIBRARY_ID`. Optional embedding keys | MIT | **Best.** Active, tests, docs, registry |
| [cookjohn/zotero-mcp](https://github.com/cookjohn/zotero-mcp) | 1083 | 2026-06-11 (`v1.5.0`) | TypeScript | Install `.xpi` from [Releases](https://github.com/cookjohn/zotero-mcp/releases); no npx/uvx | Plugin-hosted Streamable HTTP MCP inside Zotero (`http://127.0.0.1:23120/mcp`) | 20 tools: search, annotations, fulltext, collections, semantic, write_note/tag/metadata/item ([README](https://github.com/cookjohn/zotero-mcp/blob/main/README.md)) | Zotero running; enable server in plugin prefs; no zotero.org key | MIT | Healthy but last release ~2 months ago; HTTP-only |
| [kaliaboi/mcp-zotero](https://github.com/kaliaboi/mcp-zotero) | 164 | **2025-02-04** | TypeScript | `npx mcp-zotero` / `npm i -g mcp-zotero` | **Web API only** | 5: `get_collections`, `get_collection_items`, `get_item_details`, `search_library`, `get_recent` ([README](https://github.com/kaliaboi/mcp-zotero/blob/main/README.md)) | `ZOTERO_API_KEY`, `ZOTERO_USER_ID` | MIT (repo) / ISC (npm 1.0.6, published **2024-12-19**) | **Abandoned.** 413 npm downloads last month but no code since Feb 2025. On [Smithery](https://smithery.ai/servers/kaliaboi/mcp-zotero) and [mcp.so](https://mcp.so/servers/mcp-zotero) |
| [kujenga/zotero-mcp](https://github.com/kujenga/zotero-mcp) | 161 | 2026-08-07 | Python | `uvx zotero-mcp@latest`; Docker `ghcr.io/kujenga/zotero-mcp:main` | Local API or Web API via pyzotero | **3:** `zotero_search_items`, `zotero_item_metadata`, `zotero_item_fulltext` ([README](https://github.com/kujenga/zotero-mcp/blob/main/README.md)) | `ZOTERO_LOCAL=true` or `ZOTERO_API_KEY` + `ZOTERO_LIBRARY_ID` | MIT | Healthy, small, official registry (`io.github.kujenga/zotero-mcp` per README) |
| [introfini/ZotSeek](https://github.com/introfini/ZotSeek) | 187 | 2026-08-17 | TypeScript | Zotero plugin (not a standalone uvx/npx server) | Local semantic index + built-in MCP | Semantic search over the local library ([repo description](https://github.com/introfini/ZotSeek)) | Zotero running; 100% local | license field **null** on GitHub | Active, but a search plugin, not a general library MCP |
| [PiaoyangGuohai1/cli-anything-zotero](https://github.com/PiaoyangGuohai1/cli-anything-zotero) | 127 | 2026-07-28 | Python | `pip install cli-anything-zotero` (PyPI 1.2.1) | Local JS Bridge plugin + Connector + Local API | 70+ CLI commands; MCP described as “legacy via v0.9.5” ([README comparison table](https://github.com/PiaoyangGuohai1/cli-anything-zotero)) | Zotero running; privileged JS endpoint | Apache-2.0 | Active CLI; **security: JS Bridge** |
| [TonybotNi/ZotLink](https://github.com/TonybotNi/ZotLink) | 137 | **2025-10-12** | Python | `pip install zotlink` (PyPI 1.3.8, 2025-10-12) | Direct `zotero.sqlite` + storage dir | Save arXiv/CVF/Rxiv preprints with PDFs ([README](https://github.com/TonybotNi/ZotLink)) | `ZOTLINK_ZOTERO_ROOT` / `ZOTLINK_ZOTERO_DB` | MIT (PyPI) | Stale; writes the local DB |
| [gyger/mcp-pyzotero](https://github.com/gyger/mcp-pyzotero) | 56 | 2025-11-20 | Python | git + `uvx --from git+…` | Local API via pyzotero | collections / items / search / recent | Local Zotero 7 | MIT | **Retired and archived.** README tells you to use 54yyyu instead |
| [Xevos117/mcp-zotero](https://github.com/Xevos117/mcp-zotero) | 34 | 2026-03-22 (npm 1.0.9) | TypeScript | `npx @xevos117/mcp-zotero` | Web API | Search, DOI add, Unpaywall PDFs, **`inject_citations` writes .docx** ([npm](https://www.npmjs.com/package/@xevos117/mcp-zotero)) | `ZOTERO_API_KEY` + user ID | MIT | Niche (Word citation fields). 241 npm downloads last month |
| [oscardvs/zoteus](https://github.com/oscardvs/zoteus) | 25 | 2026-08-14 (v1.1.0) | TypeScript | from source | Web API v3 + local API | Broad: search, “safe writes”, DOI, CSL, semantic graph ([repo description](https://github.com/oscardvs/zoteus)) | Local and/or web credentials | MIT | Young (created 2026-05-29); watch, don’t pick yet |
| [swairshah/zotero-mcp-server](https://github.com/swairshah/zotero-mcp-server) | 29 | **2025-06-04** | Python | clone | Local library | Small local exposer | Local Zotero | Apache-2.0 | Stale |
| [RaulSimpetru/zotero-library-mcp](https://github.com/RaulSimpetru/zotero-library-mcp) | 2 | 2026-08-09 | Python | `uvx --from git+…` | Web API writes | Add by DOI / arXiv / ISBN; collections | `ZOTERO_LIBRARY_ID` + `ZOTERO_API_KEY` (write) | (no SPDX on GitHub) | Write-only specialist; on official registry |
| [danielostrow/zotero-mcp-server](https://github.com/danielostrow/zotero-mcp-server) | 6 | (repo `updated_at` 2026-05-15; 7 commits) | TypeScript | from source; npm “coming soon” | Web API | search/cite/create/update/delete ([README](https://github.com/danielostrow/zotero-mcp-server)) | `ZOTERO_API_KEY` + `ZOTERO_USER_ID` | (has LICENSE file) | Tiny, not packaged |

Not compared as general MCPs (wrong job): [papersgpt/papersgpt-for-zotero](https://github.com/papersgpt/papersgpt-for-zotero) (2,597 stars — in-Zotero chat plugin), [introfini/mcp-server-zotero-dev](https://github.com/introfini/mcp-server-zotero-dev) (Zotero *plugin development* MCP), [yilewang/llm-for-zotero](https://github.com/yilewang/llm-for-zotero) (full research agent, not a drop-in MCP).

---

## 3. Candidate notes (the four you named, plus better-maintained others)

### 54yyyu/zotero-mcp — winner

- Docs: [github.com/54yyyu/zotero-mcp](https://github.com/54yyyu/zotero-mcp), [stevenyuyy.com/zotero-mcp](https://stevenyuyy.com/zotero-mcp/), [pypi.org/project/zotero-mcp-server](https://pypi.org/project/zotero-mcp-server/), [glama.ai/mcp/servers/54yyyu/zotero-mcp](https://glama.ai/mcp/servers/54yyyu/zotero-mcp).
- Install: `uv tool install zotero-mcp-server` then `zotero-mcp setup` ([README](https://github.com/54yyyu/zotero-mcp/blob/main/README.md)).
- Optional extras: `[semantic]`, `[pdf]`, `[scite]`, `[all]`.
- Better BibTeX is **optional**, “highly recommended” only for citation-key lookup and PDF annotation extraction ([README § PDF Annotation Extraction](https://github.com/54yyyu/zotero-mcp/blob/main/README.md)).
- **Caveat vs current Zotero docs:** the README still says “The local API is fast but read-only, so the MCP server uses the Zotero web API for write operations.” Official Zotero docs now document **local writes in Zotero 10+** via a runtime-granted local API key ([Local API](https://www.zotero.org/support/dev/web_api/v3/local_api)). Zotero 10 is **currently in beta** ([Zotero 10 for Developers](https://www.zotero.org/support/dev/zotero_10_for_developers)). Homebrew stable users should keep using hybrid mode (local read + web write) until 54yyyu grows native local-write support and you are on Zotero 10 stable.
- Security surface: write tools can create/update/delete notes, merge duplicates, attach files. Keep `ZOTERO_MCP_TOOLSETS=none` (or omit writes by not setting a web API key) until you want mutations. Semantic search can call OpenAI/Gemini if you configure those keys.

### kaliaboi/mcp-zotero — do not use

- Last source commit 2025-02-04; npm `mcp-zotero@1.0.6` last published 2024-12-19 ([npm registry](https://registry.npmjs.org/mcp-zotero)).
- Web API only; five read tools; no fulltext, no annotations, no writes ([README](https://github.com/kaliaboi/mcp-zotero/blob/main/README.md)).
- Still listed on [Smithery](https://smithery.ai/servers/kaliaboi/mcp-zotero), [mcp.so](https://mcp.so/servers/mcp-zotero), [glama](https://glama.ai/mcp/servers/kaliaboi/mcp-zotero), [mcpservers.org](https://mcpservers.org/servers/kaliaboi/mcp-zotero). Registry presence ≠ maintenance.

### kujenga/zotero-mcp — best small server

- Intentionally three tools. Local or web. `uvx zotero-mcp@latest` ([README](https://github.com/kujenga/zotero-mcp/blob/main/README.md)).
- Owns the PyPI name `zotero-mcp` ([0.3.1, 2026-08-07](https://pypi.org/project/zotero-mcp/)).
- mcp.so’s default “zotero-mcp” listing is this project, and its sample config incorrectly wraps the inspector (`npx @modelcontextprotocol/inspector uv run zotero-mcp`) — use the README’s `uvx` snippet, not mcp.so’s ([mcp.so/servers/zotero-mcp](https://mcp.so/servers/zotero-mcp)).

### cookjohn/zotero-mcp — best in-Zotero plugin MCP

- Unified architecture: AI client ↔ Streamable HTTP ↔ plugin ([README](https://github.com/cookjohn/zotero-mcp/blob/main/README.md)).
- Default port **23120**, not 23119.
- Local writes without a zotero.org key (plugin talks to Zotero’s JS API).
- Requires Zotero running; Streamable HTTP support varies by client.

### Others worth knowing

- **ZotSeek** — local semantic search plugin with MCP. Complement, not replacement.
- **cli-anything-zotero** — CLI-first, JS Bridge. Powerful and a larger attack surface (privileged JS in Zotero).
- **ZotLink** — preprint ingest via sqlite. Last commit 2025-10-12. Official Zotero 10 docs say external tools “probably shouldn’t” read `zotero.sqlite` directly, especially with WAL mode ([Zotero 10 for Developers](https://www.zotero.org/support/dev/zotero_10_for_developers)).
- **gyger/mcp-pyzotero** — archived; author retired it in favor of 54yyyu ([README](https://github.com/gyger/mcp-pyzotero/blob/main/README.md)).
- **Hosted “MCP for Zotero”** (`io.github.AlejandroArnaud/mcp-for-zotero` on the [official registry](https://registry.modelcontextprotocol.io/v0.1/servers?search=zotero); discussed on [forums.zotero.org](https://forums.zotero.org/discussion/130133/mcp-for-zotero-connect-your-library-to-claude-chatgpt-and-other-ai-assistants)): you paste a zotero.org API key into a third-party HTTP endpoint. Skip for a personal local setup.

---

## 4. Agent skills

`npx skills find zotero` on 2026-08-18 (skills.sh):

| Skill | Installs | Source | What it actually does | Quality / risk |
|---|---:|---|---|---|
| [k-dense-ai/scientific-agent-skills@pyzotero](https://skills.sh/k-dense-ai/scientific-agent-skills/pyzotero) | 1.1K | [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) (33,737 stars) | Teaches pyzotero Web API CRUD. Not an MCP wrapper | Highest-quality *library* skill. Needs `ZOTERO_LIBRARY_ID` / `ZOTERO_API_KEY`. Duplicates 54yyyu if MCP is installed |
| [fuzhiyu/researchprojecttemplate@zotero-paper-reader](https://skills.sh/fuzhiyu/researchprojecttemplate/zotero-paper-reader) | 589 | same GitHub path | Workflow: MCP search → download PDF → convert to markdown | Depends on an already-configured Zotero MCP (`mcp__zotero__zotero_search_items`). Project-specific paths |
| [hkuds/cli-anything@cli-anything-zotero](https://skills.sh/hkuds/cli-anything/cli-anything-zotero) | 418 | [HKUDS/cli-anything](https://github.com/HKUDS/cli-anything) / [PiaoyangGuohai1/cli-anything-zotero](https://github.com/PiaoyangGuohai1/cli-anything-zotero) | Skill for the JS-Bridge CLI | 418 installs; inherits JS Bridge risk |
| [galaxy-dawn/claude-scholar@zotero-obsidian-bridge](https://skills.sh/galaxy-dawn/claude-scholar/zotero-obsidian-bridge) | 372 | [Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | Zotero ↔ Obsidian in a larger research suite | Too heavy if you only want library access |
| [shoei05/claude-code-zotero-skill@zotero](https://skills.sh/shoei05/claude-code-zotero-skill/zotero) | 236 | [shoei05/claude-code-zotero-skill](https://github.com/shoei05/claude-code-zotero-skill) (12 stars, last commit 2026-02-12) | curl against `:23119` + Web API; DOI import | skills.sh **Gen Agent Trust Hub: Fail**. Do not install |
| [kerim/zotero-code-execution@zotero-mcp-code](https://skills.sh/kerim/zotero-code-execution/zotero-mcp-code) | 82 | [kerim/zotero-code-execution](https://github.com/kerim/zotero-code-execution) | “Write Python that fetches 50–100+ items” instead of calling MCP | **Code-execution skill.** Passes Trust Hub, still a larger sandbox risk than a tool call |
| [openai/plugins@zotero](https://skills.sh/openai/plugins/zotero) | 3 | [openai/plugins](https://github.com/openai/plugins) (**archived**, 5,110 stars) | Codex helper `python3 …/skills/zotero/scripts/zotero.py` | Official-ish but archived repo; 3 installs. Path is under the plugins tree, not a standalone skill you should pin |

GitHub skills not (or barely) on skills.sh:

| Repo | Stars | Last commit | Role |
|---|---:|---|---|
| [WenyuChiou/zotero-skills](https://github.com/WenyuChiou/zotero-skills) (`skills/zotero-skills/SKILL.md`) | 49 | 2026-07-17 | Full CRUD skill via pyzotero dual-API (local `:23119` reads, web writes). Marketplace: `claude plugin install zotero-skills@ai-research-skills`. Best *skill-instead-of-MCP* option |
| [kerim/zotero-mcp-skill](https://github.com/kerim/zotero-mcp-skill) (`SKILL.md`) | 13 | **2025-10-25** | Wraps 54yyyu tools with multi-strategy search + **Logseq outline** output + hardcoded `/Users/niyaro/Desktop/` save path. Stale and personal |
| [ketthub/zotero-skill](https://github.com/ketthub/zotero-skill) | 8 | 2026-03-28 (initial commit only) | Zero-dep read of `~/Zotero/zotero.sqlite` with `immutable=1`. Explicitly anti-MCP. Official Zotero 10 docs discourage direct sqlite |
| [congcongwang0122/zotero-skill](https://github.com/congcongwang0122/zotero-skill) | 156 | (repo `updated_at` 2026-08-17) | Chinese “write a 10k-word review from a Zotero collection” workflow skill — not a library connector |
| [cheneternity/Zotero-Analytical-Workflow-Skills](https://github.com/cheneternity/Zotero-Analytical-Workflow-Skills) | 422 | (updated 2026-08-17) | Zotero → Obsidian reading-note pipeline |

**Skill vs MCP:** a good skill adds *policy* (how to search, how to format, when not to write). A bad skill reimplements the API badly or executes code. None of the marketplace skills are a better *connector* than 54yyyu.

---

## 5. Zotero-side requirements (macOS, Homebrew)

### Local API (port 23119) — you want this

Official docs: [Local API](https://www.zotero.org/support/dev/web_api/v3/local_api), [Web API basics](https://www.zotero.org/support/dev/web_api/v3/basics), original announcement [zotero-dev 2024-06-15](https://groups.google.com/g/zotero-dev/c/ElvHhIFAXrY/m/fA7SKKwsAgAJ).

1. Zotero desktop must be running (Homebrew cask is fine: `brew install --cask zotero`).
2. Settings → Advanced → **“Allow other applications on this computer to communicate with Zotero”**.
3. Server is `http://localhost:23119/api/`. Connector ping: `curl -s http://127.0.0.1:23119/connector/ping` ([Zotero team, forums](https://forums.zotero.org/discussion/124269/connector-not-communicating-with-zotero-app)).
4. Reads: no API key. Use user id `0` or your numeric userID ([Local API](https://www.zotero.org/support/dev/web_api/v3/local_api)).
5. Do **not** expose or forward port 23119. Official warning: “applications running locally can read the user’s library.”
6. Browser hits return “Request not allowed” unless `Zotero-Allowed-Request` is set — expected ([forums](https://forums.zotero.org/discussion/117119/is-allow-other-applications-on-this-computer-to-communicate-with-zotero-working-post-7-0)).

### Local writes — Zotero 10+ only

[Local API § Authorizing Writes](https://www.zotero.org/support/dev/web_api/v3/local_api): `POST /api/local/authorize` pops Allow / Always Allow / Deny. Key is unrelated to zotero.org keys. Zotero 10 is in beta ([Zotero 10 for Developers](https://www.zotero.org/support/dev/zotero_10_for_developers)). Homebrew stable is almost certainly still 7/8/9 — treat local as **read-only** until you upgrade.

### Web API — needed today for writes on stable Zotero

[api.zotero.org](https://www.zotero.org/support/dev/web_api/v3/start), keys at [zotero.org/settings/keys](https://www.zotero.org/settings/keys). Create a key with the least privilege you need. User ID is on that page. Writes: [Write Requests](https://www.zotero.org/support/dev/web_api/v3/write_requests).

### Plugins

| Plugin | Required? |
|---|---|
| None | Required for 54yyyu / kujenga / kaliaboi |
| [Better BibTeX](https://retorque.re/zotero-better-bibtex/installation/) | Optional. 54yyyu: citation keys + better annotation extraction |
| cookjohn MCP plugin | Only if you pick cookjohn |
| cli-anything JS Bridge | Only if you pick that CLI |
| zotero-local-api third-party plugin | **No.** Local API is built into Zotero 7+ |

### sqlite

Do not point agents at `~/Zotero/zotero.sqlite` if the local API is available. Zotero 10 enables WAL; copying/reading the main file alone can be stale or inconsistent ([Zotero 10 for Developers](https://www.zotero.org/support/dev/zotero_10_for_developers)).

---

## 6. Setup for this machine (macOS + Homebrew Zotero)

### Prerequisites

```bash
# Zotero already installed via Homebrew cask is enough.
# Confirm the app is running, then:
curl -s http://127.0.0.1:23119/connector/ping
# Expect a short "Zotero is running" style body (Zotero team example:
# https://forums.zotero.org/discussion/124269/).

# Enable: Zotero → Settings → Advanced →
# "Allow other applications on this computer to communicate with Zotero"
```

Optional writes (stable Zotero): create a key at https://www.zotero.org/settings/keys and note the numeric userID on that page.

Optional: [Better BibTeX](https://retorque.re/zotero-better-bibtex/installation/).

### Install the winner

```bash
# Do NOT run: uvx zotero-mcp          # that is kujenga's 3-tool server
uv tool install zotero-mcp-server     # 54yyyu
zotero-mcp setup                      # writes Claude Desktop config if present
zotero-mcp setup-info                 # prints the absolute binary path (GUI apps need this)
```

Semantic search later, not on day one:

```bash
uv tool install "zotero-mcp-server[semantic]"
zotero-mcp setup --semantic-config-only
zotero-mcp update-db                  # metadata-only index
```

### MCP config snippets (from the project's own README)

Local read-only (recommended first):

```json
{
  "mcpServers": {
    "zotero": {
      "command": "zotero-mcp",
      "env": {
        "ZOTERO_LOCAL": "true",
        "ZOTERO_MCP_TOOLSETS": "none"
      }
    }
  }
}
```

If the GUI client cannot see `zotero-mcp` on `PATH`, replace `command` with the absolute path from `which zotero-mcp` / `zotero-mcp setup-info` ([README tip](https://github.com/54yyyu/zotero-mcp/blob/main/README.md)).

Hybrid (local reads + web writes):

```json
{
  "mcpServers": {
    "zotero": {
      "command": "zotero-mcp",
      "env": {
        "ZOTERO_LOCAL": "true",
        "ZOTERO_API_KEY": "YOUR_API_KEY",
        "ZOTERO_LIBRARY_ID": "YOUR_USER_ID",
        "ZOTERO_LIBRARY_TYPE": "user",
        "ZOTERO_MCP_TOOLSETS": "none"
      }
    }
  }
}
```

Where to put it:

| Client | Config |
|---|---|
| Cursor | `~/.cursor/mcp.json` or project `.cursor/mcp.json` |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Code | `~/.claude.json` (`mcpServers`) or `claude mcp add` |
| Codex | `codex mcp add` (same env vars) |
| OpenCode / Goose | their stdio MCP config, same `command` + `env` |

`uvx` one-shot alternative (still 54yyyu — note the **package name**):

```json
{
  "mcpServers": {
    "zotero": {
      "command": "uvx",
      "args": ["--from", "zotero-mcp-server", "zotero-mcp"],
      "env": { "ZOTERO_LOCAL": "true", "ZOTERO_MCP_TOOLSETS": "none" }
    }
  }
}
```

If you ever want the *small* server instead:

```json
{
  "mcpServers": {
    "zotero": {
      "command": "uvx",
      "args": ["zotero-mcp@latest"],
      "env": { "ZOTERO_LOCAL": "true" }
    }
  }
}
```

That second block is [kujenga’s documented config](https://github.com/kujenga/zotero-mcp/blob/main/README.md).

### Optional local skill (recommended over marketplace)

Do not `npx skills add` a Zotero skill. Check a short `SKILL.md` into chezmoi, e.g. `~/.claude/skills/zotero/SKILL.md` / Cursor rules, with this policy:

1. Prefer MCP tools when the `zotero` server is connected.
2. On Claude Code / Codex / OpenCode, prefer `zotero-cli` (`zotero-cli search …`, `zotero-cli get metadata KEY`) to avoid paying the MCP tool-schema tax ([54yyyu README § CLI Mode](https://github.com/54yyyu/zotero-mcp/blob/main/README.md)).
3. Never read `zotero.sqlite` or write files outside the project.
4. Do not merge duplicates or delete items unless the user asked.
5. Better BibTeX citekeys are optional; fall back to item keys.

If you insist on an existing skill as a fallback for hosts without MCP: [WenyuChiou/zotero-skills](https://github.com/WenyuChiou/zotero-skills) at `skills/zotero-skills/SKILL.md`, or [k-dense-ai pyzotero](https://skills.sh/k-dense-ai/scientific-agent-skills/pyzotero) (`npx skills add https://github.com/k-dense-ai/scientific-agent-skills --skill pyzotero`). Do not install both a CRUD skill *and* 54yyyu — they will fight.

---

## 7. Security / abandonment flags

| Item | Flag | Source |
|---|---|---|
| kaliaboi/mcp-zotero | Abandoned (last commit 2025-02-04, npm 2024-12-19) | [GitHub](https://github.com/kaliaboi/mcp-zotero), [npm](https://registry.npmjs.org/mcp-zotero) |
| gyger/mcp-pyzotero | Retired + archived | [README](https://github.com/gyger/mcp-pyzotero), GitHub `archived: true` |
| stevennevins/zotero-mcp | Does not exist | GitHub search, 0 results |
| TonybotNi/ZotLink | Writes `zotero.sqlite`; stale | [README](https://github.com/TonybotNi/ZotLink), last commit 2025-10-12 |
| ketthub/zotero-skill | Direct sqlite | [README](https://github.com/ketthub/zotero-skill) |
| cli-anything-zotero JS Bridge | Privileged JS endpoint inside Zotero | [README](https://github.com/PiaoyangGuohai1/cli-anything-zotero) |
| kerim/zotero-code-execution | Instructs the agent to execute Python against large fetches | [skills.sh](https://skills.sh/kerim/zotero-code-execution/zotero-mcp-code) |
| shoei05/claude-code-zotero-skill | skills.sh Trust Hub **Fail** | [skills.sh page](https://skills.sh/shoei05/claude-code-zotero-skill/zotero) |
| Xevos117 `inject_citations` | Writes `.docx` on disk | [npm readme](https://www.npmjs.com/package/@xevos117/mcp-zotero) |
| Hosted MCP-for-Zotero | Third party holds your API key | [official registry](https://registry.modelcontextprotocol.io/v0.1/servers?search=zotero), [Zotero forums](https://forums.zotero.org/discussion/130133) |
| 54yyyu write/merge tools | Can mutate the library; keep toolsets tight | [README tool groups](https://github.com/54yyyu/zotero-mcp/blob/main/README.md) |
| Port 23119 | Local-only; do not forward | [Local API](https://www.zotero.org/support/dev/web_api/v3/local_api) |
| mcp.so default config for kujenga | Wraps MCP Inspector as the server command | [mcp.so/servers/zotero-mcp](https://mcp.so/servers/zotero-mcp) |

---

## 8. Decision summary

1. **MCP:** `zotero-mcp-server` from [54yyyu/zotero-mcp](https://github.com/54yyyu/zotero-mcp).  
2. **Skill:** none from the market. Add a tiny local skill later if agents misuse the tools.  
3. **Zotero:** Homebrew app + local API checkbox. No plugin required. Better BibTeX optional. Web API key only when you want writes.  
4. **Do not** `uvx zotero-mcp` unless you intentionally want kujenga’s 3-tool server.  
5. **Revisit** local-write support when you are on Zotero 10 stable and 54yyyu documents `POST /api/local/authorize`.

---

## Sources (primary)

- GitHub API repo + last-commit objects for 54yyyu, kujenga, kaliaboi, cookjohn, gyger, introfini/ZotSeek, PiaoyangGuohai1, kerim, WenyuChiou, ketthub, shoei05, openai/plugins, K-Dense-AI, RaulSimpetru, Xevos117, TonybotNi, swairshah, oscardvs (queried 2026-08-17/18).
- [54yyyu README](https://github.com/54yyyu/zotero-mcp/blob/main/README.md), [kujenga README](https://github.com/kujenga/zotero-mcp/blob/main/README.md), [kaliaboi README](https://github.com/kaliaboi/mcp-zotero/blob/main/README.md), [cookjohn README](https://github.com/cookjohn/zotero-mcp/blob/main/README.md), [gyger README](https://github.com/gyger/mcp-pyzotero/blob/main/README.md).
- [PyPI zotero-mcp-server](https://pypi.org/pypi/zotero-mcp-server/json), [PyPI zotero-mcp](https://pypi.org/pypi/zotero-mcp/json), [npm mcp-zotero](https://registry.npmjs.org/mcp-zotero), [npm downloads](https://api.npmjs.org/downloads/point/last-month/mcp-zotero).
- [Official MCP registry search=zotero](https://registry.modelcontextprotocol.io/v0.1/servers?search=zotero).
- [Zotero Local API](https://www.zotero.org/support/dev/web_api/v3/local_api), [Web API v3](https://www.zotero.org/support/dev/web_api/v3/basics), [Write Requests](https://www.zotero.org/support/dev/web_api/v3/write_requests), [Zotero 10 for Developers](https://www.zotero.org/support/dev/zotero_10_for_developers), [zotero-dev local API announcement](https://groups.google.com/g/zotero-dev/c/ElvHhIFAXrY/m/fA7SKKwsAgAJ).
- `npx skills find zotero` → [skills.sh](https://skills.sh) install counts, 2026-08-18.
- [Smithery kaliaboi](https://smithery.ai/servers/kaliaboi/mcp-zotero), [mcp.so kujenga](https://mcp.so/servers/zotero-mcp), [mcp.so kaliaboi](https://mcp.so/servers/mcp-zotero), [Glama 54yyyu](https://glama.ai/mcp/servers/54yyyu/zotero-mcp).
