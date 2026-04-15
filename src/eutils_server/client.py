"""Shared async client and normalization helpers for NCBI E-utilities."""

from __future__ import annotations

import asyncio
import json
import os
import time
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from eutils_server import config
from eutils_server.constants.eutils import BASE_URL, UTILITY_PATHS

REQUEST_INTERVAL_SECONDS = 0.4
DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_PREVIEW_RECORDS = 10
MAX_RETRIES = 3

_REQUEST_LOCK = asyncio.Lock()
_LAST_REQUEST_AT = 0.0
_DB_CACHE_LOCK = asyncio.Lock()
_DB_CACHE: dict[str, Any] = {"databases": None, "expires_at": 0.0}


class EUtilsClientError(Exception):
    """Raised when an E-utilities request fails."""


class EUtilsClient:
    """Small async client for read-only NCBI E-utilities access."""

    def __init__(self, base_url: str = BASE_URL, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def einfo(self, *, db: str | None = None, version: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"retmode": "json"}
        if db:
            params["db"] = db
        if version:
            params["version"] = version
        return await self._request_json(UTILITY_PATHS["einfo"], params=params)

    async def esearch(self, *, params: dict[str, Any]) -> dict[str, Any]:
        request_params = {"retmode": "json", **params}
        return await self._request_json(UTILITY_PATHS["esearch"], params=request_params)

    async def esummary(self, *, params: dict[str, Any]) -> dict[str, Any]:
        request_params = {"retmode": "json", **params}
        return await self._request_json(UTILITY_PATHS["esummary"], params=request_params)

    async def efetch(self, *, params: dict[str, Any]) -> str:
        request_params = dict(params)
        return await self._request_text(UTILITY_PATHS["efetch"], params=request_params)

    async def ensure_valid_db(self, db: str) -> None:
        databases = await self.list_databases()
        if db not in databases:
            raise EUtilsClientError(
                f"Unknown Entrez database '{db}'. Use eutils_info with no db to list supported databases."
            )

    async def list_databases(self) -> list[str]:
        async with _DB_CACHE_LOCK:
            now = time.monotonic()
            if _DB_CACHE["databases"] and now < _DB_CACHE["expires_at"]:
                return list(_DB_CACHE["databases"])

            data = await self.einfo()
            databases = data.get("einforesult", {}).get("dblist", []) or []
            _DB_CACHE["databases"] = list(databases)
            _DB_CACHE["expires_at"] = now + 3600
            return list(databases)

    async def _request_json(self, path: str, *, params: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await self._request("GET", path, params=params)
            return response.json()
        except json.JSONDecodeError as exc:
            raise EUtilsClientError("NCBI returned invalid JSON.") from exc

    async def _request_text(self, path: str, *, params: dict[str, Any]) -> str:
        response = await self._request("GET", path, params=params)
        return response.text

    async def _request(self, method: str, path: str, *, params: dict[str, Any]) -> httpx.Response:
        request_params = {key: value for key, value in params.items() if value is not None}
        request_params.update(_build_common_params())

        for attempt in range(MAX_RETRIES + 1):
            await _throttle_requests()

            try:
                response = await self._client.request(method, path, params=request_params)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429 and attempt < MAX_RETRIES:
                    await asyncio.sleep(1.0 * (2**attempt))
                    continue
                raise EUtilsClientError(_extract_error_message(exc.response)) from exc
            except httpx.HTTPError as exc:
                raise EUtilsClientError(f"Request to NCBI failed: {exc}") from exc

        raise EUtilsClientError("NCBI request failed after retries.")


async def _throttle_requests() -> None:
    global _LAST_REQUEST_AT

    async with _REQUEST_LOCK:
        now = time.monotonic()
        elapsed = now - _LAST_REQUEST_AT
        if elapsed < REQUEST_INTERVAL_SECONDS:
            await asyncio.sleep(REQUEST_INTERVAL_SECONDS - elapsed)
        _LAST_REQUEST_AT = time.monotonic()


def _build_common_params() -> dict[str, str]:
    params: dict[str, str] = {}
    api_key = config.NCBI_API_KEY or os.environ.get("NCBI_API_KEY")
    tool_name = config.NCBI_TOOL or os.environ.get("NCBI_TOOL", "mcp-server-ncbi-eutils")
    email = config.NCBI_EMAIL or os.environ.get("NCBI_EMAIL")
    if api_key:
        params["api_key"] = api_key
    if tool_name:
        params["tool"] = tool_name
    if email:
        params["email"] = email
    return params


def summarize_einfo_response(data: dict[str, Any], *, include_raw: bool) -> dict[str, Any]:
    result = data.get("einforesult", {})
    dblist = result.get("dblist", []) or []
    dbinfo_list = result.get("dbinfo", []) or []

    payload: dict[str, Any] = {
        "utility": "einfo",
        "database_count": len(dblist),
    }

    if dblist:
        payload["databases"] = dblist

    if dbinfo_list:
        dbinfo = dbinfo_list[0]
        fieldlist = dbinfo.get("fieldlist", []) or []
        linklist = dbinfo.get("linklist", []) or []
        payload["db_info"] = {
            "db": dbinfo.get("dbname"),
            "menu_name": dbinfo.get("menuname"),
            "description": dbinfo.get("description"),
            "build": dbinfo.get("dbbuild"),
            "count": _safe_int(dbinfo.get("count")),
            "last_update": dbinfo.get("lastupdate"),
            "field_count": len(fieldlist),
            "link_count": len(linklist),
        }
        payload["fields"] = [
            {
                "name": field.get("name"),
                "full_name": field.get("fullname"),
                "description": field.get("description"),
                "term_count": _safe_int(field.get("termcount")),
                "is_date": field.get("isdate") == "Y",
                "is_numerical": field.get("isnumerical") == "Y",
                "single_token": field.get("singletoken") == "Y",
                "hierarchy": field.get("hierarchy") == "Y",
                "is_hidden": field.get("ishidden") == "Y",
            }
            for field in fieldlist
        ]
        payload["links"] = [
            {
                "name": link.get("name"),
                "menu": link.get("menu"),
                "description": link.get("description"),
                "db_to": link.get("dbto"),
            }
            for link in linklist
        ]

    if include_raw:
        payload["raw"] = data
    return payload


def summarize_esearch_response(data: dict[str, Any], *, include_raw: bool) -> dict[str, Any]:
    result = data.get("esearchresult", {})
    ids = result.get("idlist", []) or []
    payload: dict[str, Any] = {
        "utility": "esearch",
        "count": _safe_int(result.get("count"), default=len(ids)),
        "retmax": _safe_int(result.get("retmax"), default=len(ids)),
        "retstart": _safe_int(result.get("retstart"), default=0),
        "ids": ids,
        "query_translation": result.get("querytranslation"),
        "translation_set": result.get("translationset", []) or [],
    }

    if result.get("webenv") and result.get("querykey"):
        payload["history"] = {
            "webenv": result.get("webenv"),
            "query_key": result.get("querykey"),
        }

    if include_raw:
        payload["raw"] = data
    return payload


def summarize_esummary_response(data: dict[str, Any], *, include_raw: bool) -> dict[str, Any]:
    result = data.get("result", {})
    uids = result.get("uids", []) or []
    summaries = [summarize_esummary_record(result.get(uid, {})) for uid in uids if result.get(uid)]

    payload: dict[str, Any] = {
        "utility": "esummary",
        "result_count": len(summaries),
        "uids": uids,
        "summaries": summaries,
    }
    if include_raw:
        payload["raw"] = data
    return payload


def summarize_esummary_record(record: dict[str, Any]) -> dict[str, Any]:
    authors = record.get("authors") or []
    article_ids = record.get("articleids") or []

    summary = {
        "uid": record.get("uid"),
        "title": record.get("title") or record.get("name"),
        "pubdate": record.get("pubdate"),
        "source": record.get("source"),
        "last_author": record.get("lastauthor"),
        "authors": [author.get("name") for author in authors if author.get("name")][:10],
        "article_ids": [
            {
                "id_type": article_id.get("idtype"),
                "value": article_id.get("value"),
            }
            for article_id in article_ids
            if article_id.get("value")
        ],
    }

    for optional_key in ("caption", "extra", "doi", "elocationid"):
        value = record.get(optional_key)
        if value:
            summary[optional_key] = value

    return summary


def summarize_efetch_response(
    payload_text: str,
    *,
    db: str,
    rettype: str | None,
    retmode: str | None,
    include_raw: bool,
) -> dict[str, Any]:
    normalized_retmode = retmode or "xml"
    payload: dict[str, Any] = {
        "utility": "efetch",
        "db": db,
        "rettype": rettype,
        "retmode": normalized_retmode,
    }

    if normalized_retmode == "xml":
        payload.update(_summarize_efetch_xml(payload_text))
    else:
        payload.update(_summarize_efetch_text(payload_text))

    if include_raw:
        payload["raw_payload"] = payload_text
    return payload


def _summarize_efetch_xml(payload_text: str) -> dict[str, Any]:
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError:
        return {
            "record_count": 0,
            "records": [],
            "warning": "NCBI returned XML that could not be parsed cleanly.",
            "preview": payload_text[:2000],
        }

    children = list(root)
    return {
        "record_count": len(children),
        "records": [_summarize_xml_record(child) for child in children[:MAX_PREVIEW_RECORDS]],
    }


def _summarize_xml_record(element: ET.Element) -> dict[str, Any]:
    record = {"record_type": _strip_namespace(element.tag)}

    pmid = element.findtext(".//PMID")
    title = element.findtext(".//ArticleTitle")
    accession = element.findtext(".//AccessionVersion")
    locus = element.findtext(".//GBSeq_locus")

    if pmid:
        record["uid"] = pmid
    if title:
        record["title"] = " ".join(title.split())
    if accession:
        record["accession"] = accession
    if locus:
        record["locus"] = locus
    if len(record) == 1:
        text_preview = "".join(element.itertext()).strip()
        if text_preview:
            record["preview"] = " ".join(text_preview.split())[:400]
    return record


def _summarize_efetch_text(payload_text: str) -> dict[str, Any]:
    lines = [line.rstrip() for line in payload_text.splitlines()]
    non_empty = [line for line in lines if line.strip()]
    return {
        "record_count": _count_text_records(payload_text),
        "preview": non_empty[:20],
    }


def _count_text_records(payload_text: str) -> int:
    chunks = [chunk for chunk in payload_text.split("\n\n") if chunk.strip()]
    return len(chunks) if chunks else 0


def _extract_error_message(response: httpx.Response) -> str:
    body = response.text.strip()
    if response.status_code == 429:
        return (
            "NCBI rate limit exceeded. Slow down requests or configure NCBI_API_KEY "
            "for higher throughput."
        )

    try:
        payload = response.json()
    except json.JSONDecodeError:
        if body:
            return f"NCBI request failed with status {response.status_code}: {body[:300]}"
        return f"NCBI request failed with status {response.status_code}."

    error = payload.get("error") or payload.get("esearchresult", {}).get("error")
    if isinstance(error, str) and error:
        return f"NCBI error: {error}"
    return f"NCBI request failed with status {response.status_code}."


def _safe_int(value: Any, default: int | None = None) -> int | None:
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _strip_namespace(tag: str) -> str:
    return tag.split("}", 1)[-1]
