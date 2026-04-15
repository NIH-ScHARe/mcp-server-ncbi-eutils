"""Initial request models for the first implementation pass."""

from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic import model_validator

from .common import HistoryContext, RawResponseOptions


class EInfoRequest(RawResponseOptions):
    db: str | None = Field(default=None, description="Entrez database name.")
    version: str | None = Field(default=None, description="Optional EInfo version, such as 2.0.")


class ESearchRequest(HistoryContext, RawResponseOptions):
    db: str = Field(description="Entrez database name.")
    term: str = Field(description="Entrez search term.")
    retstart: int = Field(default=0, ge=0, description="Offset into the result set.")
    retmax: int = Field(default=20, ge=0, le=10000, description="Maximum number of IDs to return.")
    sort: str | None = Field(default=None, description="Optional sort order supported by the database.")
    usehistory: bool = Field(default=False, description="Store the search result on the Entrez History server.")
    field: str | None = Field(default=None, description="Optional Entrez field abbreviation.")
    datetype: str | None = Field(default=None, description="Date field to filter on, such as pdat or edat.")
    mindate: str | None = Field(default=None, description="Minimum date in YYYY, YYYY/MM, or YYYY/MM/DD format.")
    maxdate: str | None = Field(default=None, description="Maximum date in YYYY, YYYY/MM, or YYYY/MM/DD format.")
    reldate: int | None = Field(default=None, ge=1, description="Number of days back from today for date filtering.")
    idtype: str | None = Field(default=None, description="Optional identifier type, when supported by the database.")


class ESummaryRequest(HistoryContext, RawResponseOptions):
    db: str = Field(description="Entrez database name.")
    ids: list[str] | None = Field(default=None, description="Explicit UIDs to summarize.")
    retstart: int = Field(default=0, ge=0, description="Offset into a history-backed result set.")
    retmax: int = Field(default=20, ge=0, le=10000, description="Maximum number of summaries to return.")
    version: str | None = Field(default=None, description="Optional summary version.")

    @model_validator(mode="after")
    def validate_id_source(self) -> "ESummaryRequest":
        if not self.ids and not self.has_history:
            raise ValueError("Provide ids or both webenv and query_key.")
        return self


class EFetchRequest(HistoryContext, RawResponseOptions):
    db: str = Field(description="Entrez database name.")
    ids: list[str] | None = Field(default=None, description="Explicit UIDs to fetch.")
    rettype: str | None = Field(default=None, description="Requested record type.")
    retmode: str | None = Field(default=None, description="Requested output format.")
    retstart: int = Field(default=0, ge=0, description="Offset into a history-backed result set.")
    retmax: int = Field(default=20, ge=0, le=10000, description="Maximum number of records to fetch.")

    @model_validator(mode="after")
    def validate_id_source(self) -> "EFetchRequest":
        if not self.ids and not self.has_history:
            raise ValueError("Provide ids or both webenv and query_key.")
        return self


class EPostRequest(RawResponseOptions):
    db: str = Field(description="Entrez database name.")
    ids: list[str] = Field(description="UIDs to upload to the Entrez History server.")


class ELinkRequest(HistoryContext, RawResponseOptions):
    dbfrom: str = Field(description="Source Entrez database.")
    db: str | None = Field(default=None, description="Optional target Entrez database.")
    ids: list[str] | None = Field(default=None, description="Explicit source UIDs.")
    linkname: str | None = Field(default=None, description="Optional named link relationship.")
    cmd: str | None = Field(default=None, description="Optional ELink command, such as neighbor or prlinks.")

    @model_validator(mode="after")
    def validate_id_source(self) -> "ELinkRequest":
        if not self.ids and not self.has_history:
            raise ValueError("Provide ids or both webenv and query_key.")
        return self


class EGQueryRequest(RawResponseOptions):
    term: str = Field(description="Cross-database query term.")


class ESpellRequest(RawResponseOptions):
    db: str | None = Field(default=None, description="Optional Entrez database.")
    term: str = Field(description="Query text to spellcheck.")


class ECitMatchRequest(RawResponseOptions):
    db: Literal["pubmed"] = Field(default="pubmed", description="Citation matching currently targets PubMed.")
    citations: list[str] = Field(
        description="Pipe-delimited citation lines in ECitMatch format: journal|year|volume|first_page|author|key."
    )


class SearchAndSummaryRequest(RawResponseOptions):
    db: str = Field(description="Entrez database name to search and summarize.")
    term: str = Field(description="Entrez search term.")
    retmax: int = Field(default=5, ge=1, le=100, description="Number of search hits to summarize.")
    sort: str | None = Field(default=None, description="Optional database-specific sort order.")
    field: str | None = Field(default=None, description="Optional Entrez field abbreviation.")
    datetype: str | None = Field(default=None, description="Date field to filter on, such as pdat or edat.")
    mindate: str | None = Field(default=None, description="Minimum date in YYYY, YYYY/MM, or YYYY/MM/DD format.")
    maxdate: str | None = Field(default=None, description="Maximum date in YYYY, YYYY/MM, or YYYY/MM/DD format.")
    reldate: int | None = Field(default=None, ge=1, description="Number of days back from today for date filtering.")
    idtype: str | None = Field(default=None, description="Optional identifier type, when supported by the database.")
    summary_version: str | None = Field(default=None, description="Optional ESummary version.")


class SearchAndFetchRequest(RawResponseOptions):
    db: str = Field(description="Entrez database name to search and fetch.")
    term: str = Field(description="Entrez search term.")
    retmax: int = Field(default=3, ge=1, le=100, description="Number of search hits to fetch.")
    sort: str | None = Field(default=None, description="Optional database-specific sort order.")
    field: str | None = Field(default=None, description="Optional Entrez field abbreviation.")
    datetype: str | None = Field(default=None, description="Date field to filter on, such as pdat or edat.")
    mindate: str | None = Field(default=None, description="Minimum date in YYYY, YYYY/MM, or YYYY/MM/DD format.")
    maxdate: str | None = Field(default=None, description="Maximum date in YYYY, YYYY/MM, or YYYY/MM/DD format.")
    reldate: int | None = Field(default=None, ge=1, description="Number of days back from today for date filtering.")
    idtype: str | None = Field(default=None, description="Optional identifier type, when supported by the database.")
    rettype: str | None = Field(default=None, description="Requested EFetch record type.")
    retmode: str | None = Field(default="text", description="Requested EFetch output format.")


class FindRelatedRequest(HistoryContext, RawResponseOptions):
    source_db: str = Field(description="Source Entrez database.")
    target_db: str = Field(description="Target Entrez database.")
    term: str | None = Field(default=None, description="Optional search term to create the source set.")
    ids: list[str] | None = Field(default=None, description="Optional explicit source UIDs.")
    source_retmax: int = Field(default=5, ge=1, le=100, description="Number of source hits to inspect.")
    related_retmax: int = Field(default=5, ge=1, le=100, description="Maximum number of related target records to summarize.")
    sort: str | None = Field(default=None, description="Optional source search sort order.")
    field: str | None = Field(default=None, description="Optional source Entrez field abbreviation.")
    datetype: str | None = Field(default=None, description="Source date field to filter on, such as pdat or edat.")
    mindate: str | None = Field(default=None, description="Minimum source date in YYYY, YYYY/MM, or YYYY/MM/DD format.")
    maxdate: str | None = Field(default=None, description="Maximum source date in YYYY, YYYY/MM, or YYYY/MM/DD format.")
    reldate: int | None = Field(default=None, ge=1, description="Number of days back from today for source date filtering.")
    idtype: str | None = Field(default=None, description="Optional source identifier type.")
    linkname: str | None = Field(default=None, description="Optional named ELink relationship.")
    cmd: str | None = Field(default=None, description="Optional ELink command.")
    summary_version: str | None = Field(default=None, description="Optional ESummary version for target summaries.")

    @model_validator(mode="after")
    def validate_source(self) -> "FindRelatedRequest":
        has_search_term = bool(self.term)
        has_ids = bool(self.ids)
        if not has_search_term and not has_ids and not self.has_history:
            raise ValueError("Provide a term, ids, or both webenv and query_key.")
        return self
