from fastapi import APIRouter, Query
from backend.services.products import get_products_service
from backend.schemas.products import ProductsResponse

router = APIRouter()

@router.get("/products", response_model=ProductsResponse)
def get_products_router(
    period: str = Query(default="all"),
    category: str = Query(default="all"),
    region: str = Query(default="all"),
    status: str = Query(default="all"),
    search: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=8, ge=1, le=50),
    sort_by: str = Query(default="date"),
    sort_order: str = Query(default="desc"),
):
    return get_products_service(period, category, region, status, search, page, page_size, sort_by, sort_order)
