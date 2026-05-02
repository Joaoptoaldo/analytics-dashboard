from fastapi import APIRouter, Query

from backend.schemas.products import ProductsResponse
from backend.services.products import get_products_service

router = APIRouter()


@router.get("/products", response_model=ProductsResponse)
def get_products_router(
    period: str = Query(default="all"),
    category: str = Query(default="all"),
    region: str = Query(default="all"),
    status: str = Query(default="all"),
    search: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=8, ge=1, le=1000),
    sort_by: str = Query(default="date"),
    sort_order: str = Query(default="desc"),
):
    """_summary_: Rota para buscar produtos com filtros, ordenação e paginação.

    Args:
        period (str, optional): _description_. Filtro de período (`30d`, `90d`, `180d`, `365d` ou `all`). Defaults to Query(default="all").
        category (str, optional): _description_. Categoria específica ou `all`. Defaults to Query(default="all").
        region (str, optional): _description_. Campo legado e ignorado no processamento. Defaults to Query(default="all").
        status (str, optional): _description_. Status específico ou `all`. Defaults to Query(default="all").
        search (str, optional): _description_. Busca textual parcial em `client` e `category`. Defaults to Query(default="").
        page (int, optional): _description_. Página atual (mínimo 1). Defaults to Query(default=1, ge=1).
        page_size (int, optional): _description_. Tamanho da página (1 a 50). Defaults to Query(default=8, ge=1, le=50).
        sort_by (str, optional): _description_. Campo de ordenação (`id`, `client`, `revenue`, `date`, `category`). Defaults to Query(default="date").
        sort_order (str, optional): _description_. Direção da ordenação (`asc` ou `desc`). Defaults to Query(default="desc").

    Returns:
        _type_: _description_: ProductsResponse com lista de itens paginada e metadados (`total`, `page`, `page_size`, `total_pages`).
    """
    if region != "all":
        import logging

        logging.warning("[DEPRECATED] region filter ignored")
    return get_products_service(period, category, region, status, search, page, page_size, sort_by, sort_order)
