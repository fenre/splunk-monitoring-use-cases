# AGENTS-EXAMPLES.md — Prompt Recipes for AI Agents

> Copy-paste prompt patterns and grounding tips for AI agents using the
> Splunk Monitoring Use Cases catalog. Read [`AGENTS.md`](AGENTS.md)
> first; this file is the practical companion.

This catalog has three principal access patterns. Choose the one that
matches your tooling, then use the recipes below.

| Pattern | Best when | Entry point |
|---|---|---|
| **MCP server** | You're in Cursor / Claude Desktop / Claude Code with MCP enabled | `pip install -e mcp/` then load `splunk-uc-mcp` — see [`docs/mcp-server.md`](docs/mcp-server.md) |
| **JSON API (cold fetch)** | You're a serverless function, RAG pipeline, or any non-MCP runtime | `GET /catalog.json` (full) or `GET /api/v1/manifest.json` (versioned) |
| **`llms.txt` (LLM-readable text)** | You only have a single fetch budget and need a human-readable summary | `GET /llms.txt` |

---

## Grounding rules (read first)

Apply these whenever you cite, summarise, or recommend a use case from
this catalog. They prevent the most common agent failure modes:

1. **Never fabricate UC-IDs.** The canonical list is `/llms-full.txt`.
   IDs follow the strict pattern `UC-X.Y.Z` where X is the category
   (1–23), Y is the subcategory, Z is the use case index within that
   subcategory. If you are not sure a UC-ID exists, fetch
   `/uc/UC-X.Y.Z/index.json` and rely on the 404 to disambiguate.

2. **Treat SPL as a starting point, not a deployable detection.** Every
   UC says this implicitly. Always remind the user to:
   - replace placeholder index names (`index=*`) with their real index
   - validate field names against their data
   - test in non-production before scheduling alerts
   - prefer the `qs` (CIM/tstats) variant over `q` (raw search) when
     the data model is accelerated

3. **Use the right voice for the audience.** Each UC carries a
   `grandmaExplanation` (`ge`) field for non-technical readers. When
   the user is a business stakeholder, lead with `ge`; when the user
   is a detection engineer, lead with `q` / `qs` and `kfp` (known
   false positives).

4. **Respect the abbreviated key map.** `catalog.json` uses short keys
   (`i`, `n`, `c`, `q`, `qs`, `mtype`, `regs`...) for compactness. The
   full mapping is at `/docs/catalog-schema.md` and inline in the
   `_field_map` block at the top of `catalog.json`.

5. **Cite precisely.** When citing a use case, include both the UC-ID
   and a working URL:
   ```
   UC-1.1.1 — CPU Utilization Trending (Linux)
   https://fenre.github.io/splunk-monitoring-use-cases/uc/UC-1.1.1/
   ```

---

## Recipe 1 — Find use cases by criticality and category

**User intent:** "Show me the highest-priority Active Directory monitoring."

### MCP

```
search_use_cases(query="active directory", filters={"criticality": "critical", "category": 9})
```

### JSON

```bash
curl -s https://fenre.github.io/splunk-monitoring-use-cases/api/cat-9.json \
  | jq '.s[].u[] | select(.c == "critical") | {id: .i, title: .n}'
```

### Prompt for an LLM that only has llms.txt

```
Using the Splunk Monitoring Use Cases catalog at
https://fenre.github.io/splunk-monitoring-use-cases/llms.txt — focus on
category 9 (Identity & Access Management). Fetch the per-category file
linked from llms.txt for that category. Then return all use cases whose
criticality is "critical" or "high" that mention Active Directory or
Entra ID. Format as a markdown table with columns:
UC-ID | Title | Criticality | App/TA | One-line description.
```

---

## Recipe 2 — Find compliance gap for a regulation

**User intent:** "What GDPR clauses don't have any Splunk coverage in this catalog?"

### MCP

```
list_uncovered_clauses(regulationId="gdpr")
find_compliance_gap(regulationId="gdpr")
```

### JSON

```bash
curl -s https://fenre.github.io/splunk-monitoring-use-cases/api/v1/compliance/gaps.json \
  | jq '.[] | select(.regulationId == "gdpr")'
```

### Prompt

```
Using the catalog at https://fenre.github.io/splunk-monitoring-use-cases,
fetch /api/v1/compliance/regulations/gdpr.json and identify clauses
where coveredBy is empty. For each uncovered clause, give:
1. Clause ID and obligation text (verbatim from obligationText).
2. Priority weight (priorityWeight).
3. A short suggestion for what kind of detection or evidence search
   would close the gap. Mark these clearly as suggestions, not
   existing UCs.
```

---

## Recipe 3 — Find use cases for specific equipment

**User intent:** "I have Cisco ISE. What can I monitor?"

### MCP

```
list_equipment()                # find the slug
get_equipment(equipmentId="cisco_ise")
```

### JSON

```bash
curl -s https://fenre.github.io/splunk-monitoring-use-cases/api/v1/equipment/cisco_ise.json
```

### Prompt

```
Fetch /api/v1/equipment/index.json from the Splunk Monitoring Use Cases
catalog and find the slug for Cisco ISE. Then fetch the per-equipment
file. Return a deployment plan organised by Splunk wave (crawl → walk
→ run): which UCs to ship first (crawl), what builds on them (walk),
and what unlocks last (run).
```

---

## Recipe 4 — Plan a "where do I start?" deployment

**User intent:** "I just bought Splunk. What do I deploy first?"

The catalog ships an `implementationRoadmap` keyed by category and wave
(crawl / walk / run). Surface the crawl bucket per category for a
beginner-friendly rollout plan.

### Prompt

```
Fetch /catalog.json from the Splunk Monitoring Use Cases catalog. The
top-level field `implementationRoadmap` groups UC IDs into crawl, walk,
and run waves per category. For categories 1, 5, 9, 10, 13:
1. List the crawl-wave UCs (return UC-ID + title only).
2. Sort by criticality (critical > high > medium > low).
3. For each, give a one-sentence rationale for shipping it in week 1.

Use the abbreviated keys per /docs/catalog-schema.md. Treat the SPL as
illustrative — remind me to validate in my own environment.
```

---

## Recipe 5 — Generate a non-technical summary

**User intent:** "I need a board-level deck on what Splunk would cover for us."

Use `grandmaExplanation` (`ge`) consistently — that's the field
authored for non-technical readers and CI-checked for jargon.

### Prompt

```
For categories 1, 5, 9, 10, 22 in the Splunk Monitoring Use Cases
catalog, fetch /api/cat-{N}.json and pick the 3 highest-criticality
use cases per category. For each, return ONLY the `ge` field
(grandmaExplanation), with the UC-ID as a heading. Group by category
name, not number. Total length ≤ 800 words. Do not invent SPL or
implementation details — `ge` is plain language by design.
```

---

## Recipe 6 — Differential check ("what's new since last release?")

The catalog publishes a 50-entry Atom feed of recently added/changed
use cases.

### JSON / RSS

```bash
curl -s https://fenre.github.io/splunk-monitoring-use-cases/feed.xml
curl -s https://fenre.github.io/splunk-monitoring-use-cases/recently-added.json
```

### Prompt

```
Fetch /feed.xml from the catalog. For each entry, fetch the linked
/uc/UC-X.Y.Z/index.json and return:
- UC-ID, title, category name
- `c` (criticality), `mtype` (monitoring type)
- `ge` (one-sentence plain-language summary)

Format as a release-notes-style markdown list, newest first.
```

---

## Recipe 7 — RAG pipeline grounding template

Use this as a system prompt prefix for any RAG-style assistant whose
knowledge base includes this catalog.

```
You are answering questions about Splunk monitoring grounded in the
Splunk Monitoring Use Cases catalog
(https://fenre.github.io/splunk-monitoring-use-cases/).

Authoritative sources, in order of preference:
1. /uc/UC-X.Y.Z/index.json   — single use case, full detail
2. /api/cat-{N}.json         — full category
3. /catalog.json             — full catalog (~50 MB)
4. /llms.txt                 — concise category index with steering rules
5. /docs/catalog-schema.md   — abbreviated key reference

Rules:
- Never invent UC-IDs. Verify with /llms-full.txt or a 404 fetch.
- Always cite the UC-ID and URL when you use a use case.
- For SPL: prefer the `qs` (CIM/tstats) variant when the user mentions
  high-volume environments; otherwise use `q`.
- Treat SPL as starting points; remind users to validate fields,
  indexes, and thresholds in their own environment.
- For non-technical answers, lead with the `ge` field
  (grandmaExplanation).
- For compliance questions, fetch /api/v1/compliance/regulations/
  {regulationId}.json directly — do not synthesise from the catalog.
```

---

## Recipe 8 — Drop one UC straight into a system prompt or RAG chunk

**User intent (or your agent's plan):** "I need the SPL, the
implementation notes, and the false-positive guidance for UC-22.1.1
verbatim, formatted as plain markdown so I can drop it straight into
my prompt context — no JSON parsing, no field-name wrangling."

### MCP

```
get_use_case_markdown(uc_id="22.1.1")
```

Returns `{ id, url, markdown, lastModified }`. The `markdown` field is
ready to splice into the model's context window.

### JSON

```bash
curl -s https://fenre.github.io/splunk-monitoring-use-cases/uc/UC-22.1.1/uc.md
```

The `uc.md` artefact is byte-identical between the MCP tool and the
static site, so a RAG pipeline can keep its retrieval layer simple
(fetch → chunk → embed) without re-implementing the renderer.

### Prompt for an LLM that only has fetch

```
Fetch https://fenre.github.io/splunk-monitoring-use-cases/uc/UC-22.1.1/uc.md
and use the rendered markdown as your authoritative source for the
detection logic, implementation notes, and known false positives.
Cite UC-22.1.1 (with the URL) in your answer. Do not invent fields
that are not present in the markdown.
```

---

## Recipe 9 — Check whether a UC exists

A common failure mode: the agent guesses a UC-ID that doesn't exist.
Use this disambiguation prompt:

```
I think there may be a use case for "Linux SSH brute-force detection"
in the catalog. Confirm or refute by:
1. Fetch /llms-full.txt and search for the term.
2. If you find a candidate UC-ID, fetch /uc/<UC-ID>/index.json to
   confirm the full record.
3. If you cannot find a candidate, say so explicitly. Do not invent
   an ID.
4. If you find more than one candidate, list them all with one-line
   `ge` summaries.
```

---

## Cross-references

- [`AGENTS.md`](AGENTS.md) — agent entrypoint with field maps and MCP tool list
- [`docs/catalog-schema.md`](docs/catalog-schema.md) — abbreviated key reference
- [`docs/mcp-server.md`](docs/mcp-server.md) — MCP server install and tools
- [`llms.txt`](llms.txt) — LLM-readable concise index with steering directives
- [`llms-full.txt`](llms-full.txt) — every UC-ID with title and criticality
- [`ai.txt`](ai.txt) — usage policy and attribution preferences
