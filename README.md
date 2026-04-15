# mcp-server-ncbi-eutils

MCP server for the NCBI Entrez E-utilities APIs.

This repository is set up to expose the current nine E-utilities as MCP tools, then add a small workflow layer for common agent tasks such as search-then-summary and search-then-fetch.

## Planned tool surface

### Core tools

These tools are intended to map closely to the underlying NCBI E-utilities.

| MCP tool | Backing utility | Purpose |
| --- | --- | --- |
| `eutils_info` | `EInfo` | Discover databases, fields, links, and database metadata. |
| `eutils_search` | `ESearch` | Search an Entrez database and return UIDs and optional history tokens. |
| `eutils_post` | `EPost` | Upload UIDs to the Entrez History server. |
| `eutils_summary` | `ESummary` | Retrieve document summaries for UIDs or history-backed result sets. |
| `eutils_fetch` | `EFetch` | Retrieve full records in supported `rettype` and `retmode` formats. |
| `eutils_link` | `ELink` | Traverse related records across or within databases. |
| `eutils_global_query` | `EGQuery` | Run a cross-database query and return counts by database. |
| `eutils_spell` | `ESpell` | Retrieve spelling suggestions for a query. |
| `eutils_citation_match` | `ECitMatch` | Resolve citation strings to PubMed identifiers. |

### Workflow helpers

These are convenience tools built on top of the core layer.

| MCP tool | Purpose |
| --- | --- |
| `eutils_search_and_summary` | Search a database and immediately summarize the matching records. |
| `eutils_search_and_fetch` | Search a database and immediately fetch the matching records. |
| `eutils_find_related` | Search or summarize a source set, then follow links to related records in a target database. |

## Tool specification

### Shared conventions

- Prefer live database validation through `EInfo` instead of a hardcoded database list.
- Support either direct identifiers (`ids`) or Entrez History inputs (`webenv`, `query_key`) when a utility allows both.
- Return both concise text and structured JSON-friendly data.
- Preserve raw upstream payloads when requested with `include_raw`.
- Include actionable error messages for invalid `db`, unsupported format combinations, or empty result sets.

### `eutils_info`

Purpose: inspect database metadata and supported search fields.

Key inputs:
- `db`: optional database name; omitted means list databases.
- `version`: optional `2.0` support for richer field metadata.

Structured output:
- `databases`
- `db_info`
- `fields`
- `links`

### `eutils_search`

Purpose: execute Entrez searches and optionally store results on the History server.

Key inputs:
- `db`
- `term`
- `retstart`
- `retmax`
- `sort`
- `usehistory`
- `field`
- `datetype`
- `mindate`
- `maxdate`
- `reldate`
- `idtype`

Structured output:
- `count`
- `ids`
- `query_translation`
- `translation_stack`
- `retstart`
- `retmax`
- `history`

### `eutils_post`

Purpose: upload UID lists to the History server for downstream calls.

Key inputs:
- `db`
- `ids`

Structured output:
- `query_key`
- `webenv`
- `count`

### `eutils_summary`

Purpose: retrieve compact summaries for records.

Key inputs:
- `db`
- `ids`
- `webenv`
- `query_key`
- `retstart`
- `retmax`
- `version`

Structured output:
- `db`
- `result_count`
- `summaries`

### `eutils_fetch`

Purpose: retrieve full records from a database.

Key inputs:
- `db`
- `ids`
- `webenv`
- `query_key`
- `rettype`
- `retmode`
- `retstart`
- `retmax`

Structured output:
- `db`
- `record_count`
- `format`
- `records` or `raw_payload`

### `eutils_link`

Purpose: retrieve related records or neighbor history sets.

Key inputs:
- `dbfrom`
- `db`
- `ids`
- `webenv`
- `query_key`
- `linkname`
- `cmd`

Structured output:
- `source_db`
- `target_db`
- `linksets`
- `history`

### `eutils_global_query`

Purpose: search globally and compare counts across databases.

Key inputs:
- `term`

Structured output:
- `term`
- `results`

### `eutils_spell`

Purpose: suggest corrected query text.

Key inputs:
- `db`
- `term`

Structured output:
- `query`
- `corrected_query`
- `replaced`

### `eutils_citation_match`

Purpose: match citation strings to PubMed records.

Key inputs:
- `citations`
- `raw`

Structured output:
- `matches`
- `unmatched`

## Planned file layout

```text
mcp-server-ncbi-eutils/
|-- README.md
|-- app.yaml
|-- main.py
|-- pyproject.toml
`-- src/
    `-- eutils_server/
        |-- __init__.py
        |-- app.py
        |-- routes.py
        |-- client.py
        |-- constants/
        |   |-- __init__.py
        |   `-- eutils.py
        |-- models/
        |   |-- __init__.py
        |   |-- common.py
        |   `-- tool_specs.py
        `-- tools/
            |-- __init__.py
            |-- core.py
            `-- workflows.py
```

## Current implementation status

- Package structure scaffolded
- Health route scaffolded
- Tool names and responsibilities specified
- `client.py` implemented with shared request handling, throttling, and retry logic
- `eutils_info`, `eutils_search`, `eutils_summary`, and `eutils_fetch` implemented
- Remaining utilities and workflow helpers still pending

## Next build order

1. Implement `eutils_post`, `eutils_link`, `eutils_global_query`, `eutils_spell`, and `eutils_citation_match`.
2. Add workflow helpers after the core tools are stable.
3. Expand normalization for non-PubMed databases and more `EFetch` format combinations.
