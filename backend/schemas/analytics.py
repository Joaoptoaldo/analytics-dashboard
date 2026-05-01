from typing import Any

from typing import Literal

from pydantic import BaseModel, Field


class AnalyticsResponse(BaseModel):
    state: Literal["valid", "no_data", "error"]
    reason: str | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)