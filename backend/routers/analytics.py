from fastapi import APIRouter, Query

from backend.schemas.analytics import AnalyticsResponse, SalesTrendResponse
from backend.services.analytics import (
    get_customers_monthly,
    get_distribution_category,
    get_sales_monthly,
    get_sales_trend,
    get_ticket_average,
    get_top_products,
)

router = APIRouter()


@router.get("/sales/monthly", response_model=AnalyticsResponse)
def sales_monthly_router(
    period: str = Query(default="all"),
    category: str = Query(default="all"),
    status: str = Query(default="all"),
    search: str = Query(default="", max_length=100),
):
    """_summary_: Retorna a série mensal de vendas agregada por mês.

    Returns:
        _type_: _description_: AnalyticsResponse com estado da operação e lista em `data` contendo os campos `month`, `revenue`, `orders` e `date_source`.
    """
    return get_sales_monthly(period=period, category=category, status=status, search=search)


@router.get("/sales/trend", response_model=SalesTrendResponse)
def sales_trend_router(
    range: str = Query(default="30d", pattern="^(30d|90d|180d|1y)$"),
    period: str = Query(default="all"),
    category: str = Query(default="all"),
    status: str = Query(default="all"),
    search: str = Query(default="", max_length=100),
):
    """_summary_: Retorna a tendência de vendas no intervalo solicitado.

    Args:
        range (str, optional): _description_. Intervalo aceito: `30d`, `90d`, `180d` ou `1y`. Defaults to Query(default="30d", pattern="^(30d|90d|180d|1y)$").

    Returns:
        _type_: _description_: SalesTrendResponse com `state`, `range` e série em `data` contendo `period`, `revenue` e `orders`.
    """
    return get_sales_trend(range_value=range, period=period, category=category, status=status, search=search)


@router.get("/distribution/category", response_model=AnalyticsResponse)
def distribution_category_router():
    """_summary_: Retorna a distribuição de registros por categoria.

    Returns:
        _type_: _description_: AnalyticsResponse com `state` e lista em `data` contendo `category` e `count`.
    """
    return get_distribution_category()


@router.get("/top/products", response_model=AnalyticsResponse)
def top_products_router(limit: int = Query(default=10, ge=1, le=50)):
    """_summary_: Retorna os produtos com maior receita.

    Args:
        limit (int, optional): _description_. Quantidade máxima de itens retornados (1 a 50). Defaults to Query(default=10, ge=1, le=50).

    Returns:
        _type_: _description_: AnalyticsResponse com `state` e lista em `data` contendo `product_id`, `product_name`, `category`, `revenue`, `status`, `date` e `date_source`.
    """
    return get_top_products(limit=limit)


@router.get("/metrics/ticket-average", response_model=AnalyticsResponse)
def ticket_average_router():
    """_summary_: Retorna a série mensal de ticket real (receita por cliente único).
    
    Fórmula: Ticket Real = SUM(revenue) / COUNT(DISTINCT clients)
    Campo `avg_ticket` reflete o valor médio que cada cliente gera por mês.

    Returns:
        _type_: _description_: AnalyticsResponse com `state` e lista em `data` contendo `month`, `avg_ticket` (ticket real em R$), `distinct_clients` (clientes únicos), `orders` e `date_source`.
    """
    return get_ticket_average()


@router.get("/customers/monthly", response_model=AnalyticsResponse)
def customers_monthly_router():
    """_summary_: Endpoint reservado para clientes por mês.

    Returns:
        _type_: _description_: AnalyticsResponse. No estado atual, retorna `error` com reason `semantically_invalid: client_is_product_name`.
    """
    return get_customers_monthly()
