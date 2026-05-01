from fastapi import APIRouter, Query

from backend.schemas.products import ProductItem, ProductsResponse
from backend.services.external import fetch_external_products, get_persisted_products, sync_external_products

router = APIRouter()


@router.get("/external-products", response_model=ProductsResponse)
def get_external_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=8, ge=1, le=50),
    sort_by: str = Query(default="date"),
    sort_order: str = Query(default="desc"),
):
    """_summary_: Retorna produtos persistidos no banco local com paginação e ordenação.

    Args:
        page (int, optional): _description_. Página atual (mínimo 1). Defaults to Query(default=1, ge=1).
        page_size (int, optional): _description_. Tamanho da página (1 a 50). Defaults to Query(default=8, ge=1, le=50).
        sort_by (str, optional): _description_. Campo de ordenação (`id`, `client`, `category`, `revenue`, `status`, `date`). Defaults to Query(default="date").
        sort_order (str, optional): _description_. Direção da ordenação (`asc` ou `desc`). Defaults to Query(default="desc").

    Returns:
        _type_: _description_: ProductsResponse com itens persistidos (`id`, `client`, `category`, `revenue`, `status`, `date`) e metadados de paginação.
    """
    rows = get_persisted_products()
    reverse = sort_order == "desc"
    if sort_by in {"id", "client", "category", "revenue", "status", "date"}:
        # Ordenação NULL-safe: None sempre no final
        def null_safe(val):
            v = val[sort_by]
            # Para datas, garantir que None sempre vá para o final
            if v is None:
                return (1, None)
            return (0, v)

        rows = sorted(rows, key=null_safe, reverse=reverse)
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
