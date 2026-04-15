"""Initial request models for the first implementation pass."""

from __future__ import annotations

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
