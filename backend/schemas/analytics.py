from typing import Any, Literal

from pydantic import BaseModel, Field


class AnalyticsResponse(BaseModel):
    state: Literal["valid", "no_data", "error"]
    reason: str | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)


class SalesTrendPoint(BaseModel):
    period: str
    revenue: float | None = None
    orders: int | None = None


class SalesTrendResponse(BaseModel):
    state: Literal["valid", "no_data", "error"]
    range: Literal["30d", "90d", "180d", "1y"]
    reason: str | None = None
    data: list[SalesTrendPoint] = Field(default_factory=list)