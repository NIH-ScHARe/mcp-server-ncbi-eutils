"""Core tool registrations for direct E-utility coverage."""

from __future__ import annotations

import json

from fastmcp import FastMCP

from eutils_server.client import (
    EUtilsClient,
    EUtilsClientError,
    summarize_efetch_response,
    summarize_einfo_response,
    summarize_esearch_response,
    summarize_esummary_response,
)
from eutils_server.models.tool_specs import (
    EFetchRequest,
    EInfoRequest,
    ESearchRequest,
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
