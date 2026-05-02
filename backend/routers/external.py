from fastapi import APIRouter, Query

from backend.schemas.products import ProductsResponse
from backend.services.external import sync_external_products
from backend.services.products import get_products_service

router = APIRouter()


@router.get("/external-products", response_model=ProductsResponse)
def get_external_products(
    period: str = Query(default="all"),
    category: str = Query(default="all"),
    status: str = Query(default="all"),
    search: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=8, ge=1, le=1000),
    sort_by: str = Query(default="date"),
    sort_order: str = Query(default="desc"),
):
    """_summary_: Endpoint para buscar produtos com filtros, ordenação e paginação. Este endpoint é destinado a produtos externos e ignora o filtro de região, que é um campo legado. Ele utiliza o serviço `get_products_service` para realizar a consulta ao banco de dados com os parâmetros fornecidos.

    Args:
        period (str, optional): _description_. Defaults to Query(default="all").
        category (str, optional): _description_. Defaults to Query(default="all").
        status (str, optional): _description_. Defaults to Query(default="all").
        search (str, optional): _description_. Defaults to Query(default="").
        page (int, optional): _description_. Defaults to Query(default=1, ge=1).
        page_size (int, optional): _description_. Defaults to Query(default=8, ge=1, le=50).
        sort_by (str, optional): _description_. Defaults to Query(default="date").
        sort_order (str, optional): _description_. Defaults to Query(default="desc").

    Returns:
        _type_: _description_: ProductsResponse com itens paginados e metadados (`total`, `page`, `page_size`, `total_pages`).
    """
    return get_products_service(period, category, "all", status, search, page, page_size, sort_by, sort_order)
