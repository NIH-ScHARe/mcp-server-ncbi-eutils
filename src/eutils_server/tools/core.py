"""Core tool registrations for direct E-utility coverage."""

from __future__ import annotations

import json

from fastmcp import FastMCP

from eutils_server.client import (
    EUtilsClient,
    EUtilsClientError,
    summarize_ecitmatch_response,
    summarize_efetch_response,
    summarize_einfo_response,
    summarize_egquery_response,
    summarize_elink_response,
    summarize_epost_response,
    summarize_esearch_response,
    summarize_espell_response,
    summarize_esummary_response,
)
from eutils_server.models.tool_specs import (
    ECitMatchRequest,
    EFetchRequest,
    EGQueryRequest,
    EInfoRequest,
    ELinkRequest,
    EPostRequest,
    ESearchRequest,
    ESpellRequest,
    ESummaryRequest,
)


def register_core_tools(mcp: FastMCP) -> None:
    """Register the first-pass core E-utility tools."""

    @mcp.tool(
        name="eutils_info",
        annotations={
            "title": "Get NCBI Entrez Database Metadata",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def eutils_info(params: EInfoRequest) -> str:
        """Inspect Entrez databases, search fields, and link metadata."""
        client = EUtilsClient()
        try:
            if params.db:
                await client.ensure_valid_db(params.db)
            data = await client.einfo(db=params.db, version=params.version)
            return json.dumps(
                summarize_einfo_response(data, include_raw=params.include_raw),
                indent=2,
            )
        except EUtilsClientError as exc:
            return json.dumps({"error": str(exc)}, indent=2)
        finally:
            await client.close()

    @mcp.tool(
        name="eutils_search",
        annotations={
            "title": "Search an NCBI Entrez Database",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def eutils_search(params: ESearchRequest) -> str:
        """Search an Entrez database and optionally store the result on the History server."""
        client = EUtilsClient()
        try:
            await client.ensure_valid_db(params.db)
            request_params = {
                "db": params.db,
                "term": params.term,
                "retstart": params.retstart,
                "retmax": params.retmax,
                "sort": params.sort,
                "usehistory": "y" if params.usehistory else None,
                "field": params.field,
                "datetype": params.datetype,
                "mindate": params.mindate,
                "maxdate": params.maxdate,
                "reldate": params.reldate,
                "idtype": params.idtype,
            }
            data = await client.esearch(params=request_params)
            return json.dumps(
                summarize_esearch_response(data, include_raw=params.include_raw),
                indent=2,
            )
        except EUtilsClientError as exc:
            return json.dumps({"error": str(exc)}, indent=2)
        finally:
            await client.close()

    @mcp.tool(
        name="eutils_summary",
        annotations={
            "title": "Get NCBI Entrez Document Summaries",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def eutils_summary(params: ESummaryRequest) -> str:
        """Retrieve compact summaries for explicit UIDs or a History-backed result set."""
        client = EUtilsClient()
        try:
            await client.ensure_valid_db(params.db)
            request_params = {
                "db": params.db,
                "id": ",".join(params.ids) if params.ids else None,
                "webenv": params.webenv,
                "query_key": params.query_key,
                "retstart": params.retstart,
                "retmax": params.retmax,
                "version": params.version,
            }
            data = await client.esummary(params=request_params)
            payload = summarize_esummary_response(data, include_raw=params.include_raw)
            payload["db"] = params.db
            return json.dumps(payload, indent=2)
        except EUtilsClientError as exc:
            return json.dumps({"error": str(exc)}, indent=2)
        finally:
            await client.close()

    @mcp.tool(
        name="eutils_fetch",
        annotations={
            "title": "Fetch Full NCBI Entrez Records",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def eutils_fetch(params: EFetchRequest) -> str:
        """Fetch full records from an Entrez database in XML or text form."""
        client = EUtilsClient()
        try:
            await client.ensure_valid_db(params.db)
            request_params = {
                "db": params.db,
                "id": ",".join(params.ids) if params.ids else None,
                "webenv": params.webenv,
                "query_key": params.query_key,
                "rettype": params.rettype,
                "retmode": params.retmode or "xml",
                "retstart": params.retstart,
                "retmax": params.retmax,
            }
            payload_text = await client.efetch(params=request_params)
            return json.dumps(
                summarize_efetch_response(
                    payload_text,
                    db=params.db,
                    rettype=params.rettype,
                    retmode=params.retmode,
                    include_raw=params.include_raw,
                ),
                indent=2,
            )
        except EUtilsClientError as exc:
            return json.dumps({"error": str(exc)}, indent=2)
        finally:
            await client.close()

    @mcp.tool(
        name="eutils_post",
        annotations={
            "title": "Post UIDs to the NCBI History Server",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def eutils_post(params: EPostRequest) -> str:
        """Upload explicit UIDs to the Entrez History server."""
        client = EUtilsClient()
        try:
            await client.ensure_valid_db(params.db)
            payload_text = await client.epost(
                params={
                    "db": params.db,
                    "id": ",".join(params.ids),
                }
            )
            return json.dumps(
                summarize_epost_response(
                    payload_text,
                    db=params.db,
                    ids=params.ids,
                    include_raw=params.include_raw,
                ),
                indent=2,
            )
        except EUtilsClientError as exc:
            return json.dumps({"error": str(exc)}, indent=2)
        finally:
            await client.close()

    @mcp.tool(
        name="eutils_link",
        annotations={
            "title": "Find Related NCBI Entrez Records",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def eutils_link(params: ELinkRequest) -> str:
        """Traverse related records within or across Entrez databases."""
        client = EUtilsClient()
        try:
            await client.ensure_valid_db(params.dbfrom)
            if params.db:
                await client.ensure_valid_db(params.db)
            data = await client.elink(
                params={
                    "dbfrom": params.dbfrom,
                    "db": params.db,
                    "id": ",".join(params.ids) if params.ids else None,
                    "webenv": params.webenv,
                    "query_key": params.query_key,
                    "linkname": params.linkname,
                    "cmd": params.cmd,
                }
            )
            return json.dumps(
                summarize_elink_response(data, include_raw=params.include_raw),
                indent=2,
            )
        except EUtilsClientError as exc:
            return json.dumps({"error": str(exc)}, indent=2)
        finally:
            await client.close()

    @mcp.tool(
        name="eutils_global_query",
        annotations={
            "title": "Run an NCBI Global Query Across Databases",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def eutils_global_query(params: EGQueryRequest) -> str:
        """Search across Entrez databases and return counts by database."""
        client = EUtilsClient()
        try:
            html = await client.egquery(term=params.term)
            return json.dumps(
                summarize_egquery_response(html, term=params.term, include_raw=params.include_raw),
                indent=2,
            )
        except EUtilsClientError as exc:
            return json.dumps({"error": str(exc)}, indent=2)
        finally:
            await client.close()

    @mcp.tool(
        name="eutils_spell",
        annotations={
            "title": "Spellcheck an NCBI Entrez Query",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def eutils_spell(params: ESpellRequest) -> str:
        """Return spelling suggestions for an Entrez query."""
        client = EUtilsClient()
        try:
            if params.db:
                await client.ensure_valid_db(params.db)
            payload_text = await client.espell(
                params={
                    "db": params.db,
                    "term": params.term,
                }
            )
            return json.dumps(
                summarize_espell_response(payload_text, include_raw=params.include_raw),
                indent=2,
            )
        except EUtilsClientError as exc:
            return json.dumps({"error": str(exc)}, indent=2)
        finally:
            await client.close()

    @mcp.tool(
        name="eutils_citation_match",
        annotations={
            "title": "Match Citations to PubMed Records",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def eutils_citation_match(params: ECitMatchRequest) -> str:
        """Resolve citation strings to PubMed IDs using ECitMatch."""
        client = EUtilsClient()
        try:
            payload_text = await client.ecitmatch(
                params={
                    "db": params.db,
                    "retmode": "xml",
                    "bdata": "\r".join(params.citations),
                }
            )
            return json.dumps(
                summarize_ecitmatch_response(
                    payload_text,
                    citations=params.citations,
                    include_raw=params.include_raw,
                ),
                indent=2,
            )
        except EUtilsClientError as exc:
            return json.dumps({"error": str(exc)}, indent=2)
        finally:
            await client.close()
