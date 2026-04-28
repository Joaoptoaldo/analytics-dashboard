from backend.data import _apply_filters, DATASET
from backend.schemas.products import ProductsResponse, ProductItem

def get_products_service(period, category, region, status, search, page, page_size, sort_by, sort_order):
    filtered = _apply_filters(DATASET, period, category, region, status, search)
    reverse = sort_order == "desc"
    if sort_by in {"id", "client", "category", "revenue", "status", "region", "date"}:
        filtered = sorted(filtered, key=lambda x: x[sort_by], reverse=reverse)
    total = len(filtered)
    total_pages = max((total + page_size - 1) // page_size, 1)
    if page > total_pages:
        page = total_pages
    start = (page - 1) * page_size
    items = filtered[start : start + page_size]
    return ProductsResponse(
        items=[ProductItem(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
