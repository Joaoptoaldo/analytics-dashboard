from pydantic import BaseModel
from typing import List

class ProductItem(BaseModel):
    id: int
    client: str
    category: str
    revenue: float
    status: str
    region: str
    date: str

class ProductsResponse(BaseModel):
    items: List[ProductItem]
    total: int
    page: int
    page_size: int
    total_pages: int
