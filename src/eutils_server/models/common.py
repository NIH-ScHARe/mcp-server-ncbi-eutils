"""Shared model primitives for E-utilities tools."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field
from pydantic import model_validator


class HistoryContext(BaseModel):
    """Reference to a result set stored on the Entrez History server."""

    webenv: str | None = Field(default=None, description="Entrez history WebEnv token.")
    query_key: str | None = Field(default=None, description="Entrez history query_key value.")

    @property
    def has_history(self) -> bool:
        return bool(self.webenv and self.query_key)

    @model_validator(mode="after")
    def validate_history_pair(self) -> "HistoryContext":
        has_webenv = bool(self.webenv)
        has_query_key = bool(self.query_key)
        if has_webenv != has_query_key:
            raise ValueError("Provide both webenv and query_key together.")
        return self


class RawResponseOptions(BaseModel):
    """Common flags that control response verbosity."""

    include_raw: bool = Field(
        default=False,
        description="Include the raw upstream payload alongside normalized output.",
    )


RetMode = Literal["xml", "json", "text", "asn.1"]
