from pydantic import BaseModel
from typing import List

class ProductItem(BaseModel):
    id: int
    client: str
    category: str
    revenue: float
    status: str
    date: str | None

class ProductsResponse(BaseModel):
    items: List[ProductItem]
    total: int
    page: int
    page_size: int
    total_pages: int
