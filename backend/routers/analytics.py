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
def sales_monthly_router():
    """_summary_: rota para obter a distribuição mensal de vendas, agrupando por mês e somando a receita total e contando o número de pedidos para cada mês. A rota retorna um dicionário contendo o estado do resultado (valid, no_data ou error), uma lista de meses com a receita total e contagem de pedidos para cada mês (se o estado for valid), ou uma razão detalhada para o estado no_data ou error. O campo "data" contém a lista de meses, receitas e contagens apenas quando o estado é "valid". Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos para calcular a distribuição mensal de vendas. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento.

    Returns:
        _type_: _description_: dicionário contendo o estado do resultado (valid, no_data ou error), uma lista de meses com a receita total e contagem de pedidos para cada mês (se o estado for valid), ou uma razão detalhada para o estado no_data ou error. O campo "data" contém a lista de meses, receitas e contagens apenas quando o estado é "valid". Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos para calcular a distribuição mensal de vendas. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento.
    """
    return get_sales_monthly()


@router.get("/sales/trend", response_model=SalesTrendResponse)
def sales_trend_router(range: str = Query(default="30d", pattern="^(30d|90d|180d|1y)$")):
    """_summary_: rota para obter a tendência de vendas em um determinado intervalo de tempo, agrupando os produtos em buckets diários, semanais ou mensais com base no intervalo selecionado. A rota retorna um dicionário contendo o estado do resultado (valid, no_data ou error), uma lista de períodos com a receita total e contagem de pedidos para cada período (se o estado for valid), ou uma razão detalhada para o estado no_data ou error. O campo "data" contém a lista de períodos, receitas e contagens apenas quando o estado é "valid". Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos para calcular a tendência de vendas. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento.

    Args:
        range (str, optional): _description_. Defaults to Query(default="30d", pattern="^(30d|90d|180d|1y)$").: intervalo de tempo para calcular a tendência de vendas

    Returns:
        _type_: _description_: dicionário contendo o estado do resultado (valid, no_data ou error), uma lista de períodos com a receita total e contagem de pedidos para cada período (se o estado for valid), ou uma razão detalhada para o estado no_data ou error. O campo "data" contém a lista de períodos, receitas e contagens apenas quando o estado é "valid". Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos para calcular a tendência de vendas. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento.
    """
    return get_sales_trend(range_value=range)


@router.get("/distribution/category", response_model=AnalyticsResponse)
def distribution_category_router():
    """_summary_: rota para obter a distribuição de produtos por categoria, agrupando os produtos por categoria e contando o número de produtos em cada categoria. A rota retorna um dicionário contendo o estado do resultado (valid, no_data ou error), uma lista de categorias com a contagem de produtos para cada categoria (se o estado for valid), ou uma razão detalhada para o estado no_data ou error. O campo "data" contém a lista de categorias e contagens apenas quando o estado é "valid". Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos para calcular a distribuição por categoria. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento.

    Returns:
        _type_: _description_: dicionário contendo o estado do resultado (valid, no_data ou error), uma lista de categorias com a contagem de produtos para cada categoria (se o estado for valid), ou uma razão detalhada para o estado no_data ou error. O campo "data" contém a lista de categorias e contagens apenas quando o estado é "valid". Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos para calcular a distribuição por categoria. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento.
    """
    return get_distribution_category()


@router.get("/top/products", response_model=AnalyticsResponse)
def top_products_router(limit: int = Query(default=10, ge=1, le=50)):
    """_summary_: rota para obter os produtos mais vendidos, ordenando os produtos pela receita total e retornando os top N produtos com base no limite especificado. A rota retorna um dicionário contendo o estado do resultado (valid, no_data ou error), uma lista dos produtos mais vendidos com suas respectivas receitas e contagens (se o estado for valid), ou uma razão detalhada para o estado no_data ou error. O campo "data" contém a lista dos produtos mais vendidos apenas quando o estado é "valid". Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos para calcular os produtos mais vendidos. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento.

    Args:
        limit (int, optional): _description_. Defaults to Query(default=10, ge=1, le=50).: número de produtos mais vendidos a serem retornados, com um valor padrão de 10 e limites mínimo de 1 e máximo de 50.

    Returns:
        _type_: _description_: dicionário contendo o estado do resultado (valid, no_data ou error), uma lista dos produtos mais vendidos com suas respectivas receitas e contagens (se o estado for valid), ou uma razão detalhada para o estado no_data ou error. O campo "data" contém a lista dos produtos mais vendidos apenas quando o estado é "valid". Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos para calcular os produtos mais vendidos. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento.
    """
    return get_top_products(limit=limit)


@router.get("/metrics/ticket-average", response_model=AnalyticsResponse)
def ticket_average_router():
    """_summary_: rota para obter o valor médio do ticket, calculando a média da receita por pedido. A rota retorna um dicionário contendo o estado do resultado (valid, no_data ou error), o valor médio do ticket (se o estado for valid), ou uma razão detalhada para o estado no_data ou error. O campo "value" contém o valor médio do ticket apenas quando o estado é "valid". Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos para calcular a média do ticket. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento.

    Returns:
        _type_: _description_: dicionário contendo o estado do resultado (valid, no_data ou error), o valor médio do ticket (se o estado for valid), ou uma razão detalhada para o estado no_data ou error. O campo "value" contém o valor médio do ticket apenas quando o estado é "valid". Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos para calcular a média do ticket. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento.
    """
    return get_ticket_average()


@router.get("/customers/monthly", response_model=AnalyticsResponse)
def customers_monthly_router():
    """_summary_: rota para obter a distribuição mensal de clientes, agrupando por mês e contando o número de clientes distintos (baseado no campo client)

    Returns:
        _type_: _description_: dicionário contendo o estado do resultado (valid, no_data ou error), uma lista de meses com a contagem de clientes distintos para cada mês (se o estado for valid), ou uma razão detalhada para o estado no_data ou error. O campo "data" contém a lista de meses e contagens de clientes apenas quando o estado é "valid". Se o estado for "no_data", o campo "reason" explica a ausência de dados válidos para calcular a distribuição mensal de clientes. Se o estado for "error", o campo "reason" fornece detalhes sobre a falha na consulta ou processamento.
    """
    return get_customers_monthly()
