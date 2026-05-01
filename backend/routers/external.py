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
    """_summary_: rota para obter os produtos persistidos no banco de dados local, retornando uma lista de dicionários com os campos id, client, category, revenue, status e date. O campo date é formatado como string no formato YYYY-MM-DD. Este método é útil para verificar os dados que foram sincronizados a partir da API externa e estão disponíveis para consulta no banco de dados local.

    Args:
        page (int, optional): _description_. Defaults to Query(default=1, ge=1).: número da página a ser retornada, com um valor padrão de 1 e limite mínimo de 1.
        page_size (int, optional): _description_. Defaults to Query(default=8, ge=1, le=50).: número de itens por página, com um valor padrão de 8 e limites mínimo de 1 e máximo de 50.
        sort_by (str, optional): _description_. Defaults to Query(default="date").: campo pelo qual os produtos devem ser ordenados, com um valor padrão de "date". Os campos permitidos para ordenação são: id, client, category, revenue, status e date. Se um campo inválido for fornecido, a ordenação será feita por date.
        sort_order (str, optional): _description_. Defaults to Query(default="desc").: ordem de ordenação dos produtos, com um valor padrão de "desc". Os valores permitidos são "asc" para ordenação ascendente e "desc" para ordenação descendente. Se um valor inválido for fornecido, a ordenação será feita em ordem descendente.

    Returns:
        _type_: _description_: ProductsResponse com lista de produtos e metadados de paginação. O campo "items" contém a lista de produtos para a página solicitada, cada um com os campos id, client, category, revenue, status e date (formatado como string no formato YYYY-MM-DD). Os campos "total", "page", "page_size" e "total_pages" fornecem informações sobre a paginação dos resultados. Se ocorrer algum erro durante o processo, a rota deve lançar uma exceção apropriada.
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
