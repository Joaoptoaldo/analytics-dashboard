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
    """_summary_: rota para buscar produtos com filtros, ordenação e paginação. Os filtros disponíveis são: period (30d, 90d, 180d, 365d ou all), category (Electronics, Clothing, Home, Sports ou all), region (North, South, East, West ou all - DEPRECATED), status (active, inactive, pending ou all) e search (termo de busca para client ou category). A ordenação pode ser feita por id, client, revenue, date ou category, e a ordem pode ser ascendente (asc) ou descendente (desc). A paginação é controlada pelos parâmetros page (número da página) e page_size (número de itens por página). A rota retorna um ProductsResponse contendo a lista de produtos para a página solicitada e metadados de paginação.

    Args:
        period (str, optional): _description_. Defaults to Query(default="all").: 30d, 90d, 180d, 365d ou all
        category (str, optional): _description_. Defaults to Query(default="all").: Electronics, Clothing, Home, Sports ou all
        region (str, optional): _description_. Defaults to Query(default="all").: North, South, East, West ou all (DEPRECATED)
        status (str, optional): _description_. Defaults to Query(default="all").: active, inactive, pending ou all
        search (str, optional): _description_. Defaults to Query(default="").: termo de busca para client ou category
        page (int, optional): _description_. Defaults to Query(default=1, ge=1).: número da página a ser retornada, com um valor padrão de 1 e limite mínimo de 1.
        page_size (int, optional): _description_. Defaults to Query(default=8, ge=1, le=50).: número de itens por página, com um valor padrão de 8 e limites mínimo de 1 e máximo de 50.
        sort_by (str, optional): _description_. Defaults to Query(default="date").: campo pelo qual os produtos devem ser ordenados, com um valor padrão de "date". Os campos permitidos para ordenação são: id, client, category, revenue, status e date. Se um campo inválido for fornecido, a ordenação será feita por date.
        sort_order (str, optional): _description_. Defaults to Query(default="desc").: ordem de ordenação dos produtos, com um valor padrão de "desc".

    Returns:
        _type_: _description_: ProductsResponse com lista de produtos e metadados de paginação. O campo "items" contém a lista de produtos para a página solicitada, cada um com os campos id, client, category, revenue, status e date (formatado como string no formato YYYY-MM-DD). Os campos "total", "page", "page_size" e "total_pages" fornecem informações sobre a paginação dos resultados. Se ocorrer algum erro durante o processo, a rota deve lançar uma exceção apropriada.
    """
    if region != "all":
        import logging

        logging.warning("[DEPRECATED] region filter ignored")
    return get_products_service(period, category, region, status, search, page, page_size, sort_by, sort_order)
