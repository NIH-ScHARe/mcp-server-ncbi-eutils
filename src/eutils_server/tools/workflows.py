"""Workflow-oriented tool registrations built on top of the core utilities."""

from __future__ import annotations

import json

from fastmcp import FastMCP

from eutils_server.client import (
    EUtilsClient,
    EUtilsClientError,
    summarize_efetch_response,
    summarize_elink_response,
    summarize_esearch_response,
    summarize_esummary_response,
)
from eutils_server.models.tool_specs import (
    FindRelatedRequest,
    SearchAndFetchRequest,
    SearchAndSummaryRequest,
)


def register_workflow_tools(mcp: FastMCP) -> None:
    """Register higher-level workflow helpers."""

    @mcp.tool(
        name="eutils_search_and_summary",
        annotations={
            "title": "Search and Summarize NCBI Records",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def eutils_search_and_summary(params: SearchAndSummaryRequest) -> str:
        """Search a database and immediately summarize the top matching records."""
        client = EUtilsClient()
        try:
            await client.ensure_valid_db(params.db)
            search_data = await client.esearch(
                params={
                    "db": params.db,
                    "term": params.term,
                    "retmax": params.retmax,
                    "sort": params.sort,
                    "field": params.field,
                    "datetype": params.datetype,
                    "mindate": params.mindate,
                    "maxdate": params.maxdate,
                    "reldate": params.reldate,
                    "idtype": params.idtype,
                }
            )
            search_payload = summarize_esearch_response(search_data, include_raw=params.include_raw)
            ids = search_payload.get("ids", [])
            response = {
                "workflow": "search_and_summary",
                "db": params.db,
                "term": params.term,
                "search": search_payload,
                "summary": {
                    "utility": "esummary",
                    "result_count": 0,
                    "uids": [],
                    "summaries": [],
                },
            }
            if ids:
                summary_data = await client.esummary(
                    params={
                        "db": params.db,
                        "id": ",".join(ids),
                        "retmax": len(ids),
                        "version": params.summary_version,
                    }
                )
                summary_payload = summarize_esummary_response(summary_data, include_raw=params.include_raw)
                summary_payload["db"] = params.db
                response["summary"] = summary_payload
            return json.dumps(response, indent=2)
        except EUtilsClientError as exc:
            return json.dumps({"error": str(exc)}, indent=2)
        finally:
            await client.close()

    @mcp.tool(
        name="eutils_search_and_fetch",
        annotations={
            "title": "Search and Fetch NCBI Records",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def eutils_search_and_fetch(params: SearchAndFetchRequest) -> str:
        """Search a database and immediately fetch the top matching records."""
        client = EUtilsClient()
        try:
            await client.ensure_valid_db(params.db)
            search_data = await client.esearch(
                params={
                    "db": params.db,
                    "term": params.term,
                    "retmax": params.retmax,
                    "sort": params.sort,
                    "field": params.field,
                    "datetype": params.datetype,
                    "mindate": params.mindate,
                    "maxdate": params.maxdate,
                    "reldate": params.reldate,
                    "idtype": params.idtype,
                }
            )
            search_payload = summarize_esearch_response(search_data, include_raw=params.include_raw)
            ids = search_payload.get("ids", [])
            response = {
                "workflow": "search_and_fetch",
                "db": params.db,
                "term": params.term,
                "search": search_payload,
                "fetch": {
                    "utility": "efetch",
                    "db": params.db,
                    "rettype": params.rettype,
                    "retmode": params.retmode or "text",
                    "record_count": 0,
                },
            }
            if ids:
                fetch_text = await client.efetch(
                    params={
                        "db": params.db,
                        "id": ",".join(ids),
                        "rettype": params.rettype,
                        "retmode": params.retmode or "text",
                        "retmax": len(ids),
                    }
                )
                response["fetch"] = summarize_efetch_response(
                    fetch_text,
                    db=params.db,
                    rettype=params.rettype,
                    retmode=params.retmode,
                    include_raw=params.include_raw,
                )
            return json.dumps(response, indent=2)
        except EUtilsClientError as exc:
            return json.dumps({"error": str(exc)}, indent=2)
        finally:
            await client.close()

    @mcp.tool(
        name="eutils_find_related",
        annotations={
            "title": "Find Related NCBI Records Across Databases",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def eutils_find_related(params: FindRelatedRequest) -> str:
        """Find related records in a target database from a source set and summarize the top targets."""
        client = EUtilsClient()
        try:
            await client.ensure_valid_db(params.source_db)
            await client.ensure_valid_db(params.target_db)

            source_payload: dict[str, object]
            source_ids: list[str] = []

            if params.term:
                search_data = await client.esearch(
                    params={
                        "db": params.source_db,
                        "term": params.term,
                        "retmax": params.source_retmax,
                        "sort": params.sort,
                        "field": params.field,
                        "datetype": params.datetype,
                        "mindate": params.mindate,
                        "maxdate": params.maxdate,
                        "reldate": params.reldate,
                        "idtype": params.idtype,
                        "usehistory": "y",
                    }
                )
                source_payload = summarize_esearch_response(search_data, include_raw=params.include_raw)
                source_ids = list(source_payload.get("ids", []))
            elif params.ids:
                source_ids = params.ids
                source_payload = {
                    "utility": "source_ids",
                    "db": params.source_db,
                    "ids": source_ids,
                }
            else:
                source_payload = {
                    "utility": "source_history",
                    "db": params.source_db,
                    "history": {
                        "webenv": params.webenv,
                        "query_key": params.query_key,
                    },
                }

            elink_data = await client.elink(
                params={
                    "dbfrom": params.source_db,
                    "db": params.target_db,
                    "id": ",".join(source_ids) if source_ids else None,
                    "webenv": params.webenv if not source_ids else None,
                    "query_key": params.query_key if not source_ids else None,
                    "linkname": params.linkname,
                    "cmd": params.cmd,
                }
            )
            link_payload = summarize_elink_response(elink_data, include_raw=params.include_raw)

            related_ids = _collect_related_ids(link_payload, target_db=params.target_db, limit=params.related_retmax)
            response = {
                "workflow": "find_related",
                "source_db": params.source_db,
                "target_db": params.target_db,
                "source": source_payload,
                "links": link_payload,
                "related_summary": {
                    "utility": "esummary",
                    "db": params.target_db,
                    "result_count": 0,
                    "uids": [],
                    "summaries": [],
                },
            }

            if related_ids:
                summary_data = await client.esummary(
                    params={
                        "db": params.target_db,
                        "id": ",".join(related_ids),
                        "retmax": len(related_ids),
                        "version": params.summary_version,
                    }
                )
                summary_payload = summarize_esummary_response(summary_data, include_raw=params.include_raw)
                summary_payload["db"] = params.target_db
                response["related_summary"] = summary_payload

            return json.dumps(response, indent=2)
        except EUtilsClientError as exc:
            return json.dumps({"error": str(exc)}, indent=2)
        finally:
            await client.close()


def _collect_related_ids(link_payload: dict[str, object], *, target_db: str, limit: int) -> list[str]:
    seen: set[str] = set()
    collected: list[str] = []

    for linkset in link_payload.get("linksets", []):
        if not isinstance(linkset, dict):
            continue
        for link_entry in linkset.get("links", []):
            if not isinstance(link_entry, dict):
                continue
            if link_entry.get("db_to") != target_db:
                continue
            for uid in link_entry.get("links", []):
                if uid not in seen:
                    seen.add(uid)
                    collected.append(uid)
                if len(collected) >= limit:
                    return collected
    return collected
