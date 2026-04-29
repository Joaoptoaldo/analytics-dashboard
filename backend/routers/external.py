from fastapi import APIRouter, Query
from backend.services.external import fetch_external_products, sync_external_products, get_persisted_products
from backend.schemas.products import ProductsResponse, ProductItem

router = APIRouter()


@router.get("/external-products", response_model=ProductsResponse)
def get_external_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=8, ge=1, le=50),
    sort_by: str = Query(default="date"),
    sort_order: str = Query(default="desc"),
):
    # Retorna apenas dados persistidos; só haverá dados após sincronização manual
    rows = get_persisted_products()
    reverse = sort_order == "desc"
    if sort_by in {"id", "client", "category", "revenue", "status", "region", "date"}:
        rows = sorted(rows, key=lambda x: x[sort_by], reverse=reverse)
    total = len(rows)
    total_pages = max((total + page_size - 1) // page_size, 1)
    if page > total_pages:
        page = total_pages
    start = (page - 1) * page_size
    items = rows[start : start + page_size]
    return ProductsResponse(
        items=[ProductItem(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
