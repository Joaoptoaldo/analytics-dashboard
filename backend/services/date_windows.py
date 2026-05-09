from __future__ import annotations
import os
from datetime import date, timedelta
from sqlalchemy import func
from backend.models.product import Product


def _env_bool(name: str, default: bool) -> bool:
    """_summary_: lê uma variável de ambiente como booleano, interpretando valores comuns de verdade (1, true, yes, on) como True e tudo mais como False, com um valor padrão caso a variável não esteja definida ou seja vazia, para facilitar a configuração de comportamentos booleanos via variáveis de ambiente de forma flexível e intuitiva

    Args:
        name (str): _description_: o nome da variável de ambiente a ser lida, que deve conter um valor representando um booleano (ex: "1", "true", "yes", "on" para True, e qualquer outro valor ou ausência para False)
        default (bool): _description_: o valor booleano a ser retornado caso a variável de ambiente não esteja definida ou seja vazia, para garantir que a função sempre retorne um valor booleano válido mesmo na ausência de configuração explícita, permitindo que o comportamento padrão seja controlado pelo código chamador

    Returns:
        bool: _description_: um valor booleano representando a interpretação da variável de ambiente, onde valores comuns de verdade são interpretados como True e tudo mais como False, com fallback para o valor padrão caso a variável não esteja definida ou seja vazia, para uso em configurações de comportamento booleano controladas por variáveis de ambiente
    """
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def get_reference_date(session) -> date:
    """_summary_: determina a data de referência para os cálculos de janela de datas, com base na configuração do ambiente `ANALYTICS_DATE_ANCHOR` que pode ser "today" (padrão) ou "latest_data", onde "today" retorna a data atual e "latest_data" retorna a data mais recente presente na tabela de produtos (excluindo sintéticos) ou a data atual se não houver dados, para permitir flexibilidade na definição da âncora temporal usada para os filtros de período nas consultas de produtos e análises, garantindo que as janelas de datas sejam calculadas corretamente com base na configuração desejada

    Args:
        session (_type_): _description_: uma sessão ativa do SQLAlchemy que pode ser usada para consultar a tabela de produtos e determinar a data mais recente presente, caso a configuração de âncora seja "latest_data", para garantir que a função possa acessar o banco de dados e retornar a data de referência correta com base na configuração do ambiente

    Returns:
        date: _description_: uma data representando a referência temporal para os cálculos de janela de datas, que pode ser a data atual ou a data mais recente presente na tabela de produtos, dependendo da configuração do ambiente `ANALYTICS_DATE_ANCHOR`, para uso nos filtros de período das consultas de produtos e análises
    """
    anchor_mode = os.getenv("ANALYTICS_DATE_ANCHOR", "today").strip().lower()
    if anchor_mode == "latest_data":
        latest_date = (
            session.query(func.max(Product.date))
            .filter(Product.is_synthetic == False)
            .scalar()
        )
        return latest_date or date.today()

    return date.today()


def apply_period_window(query, days: int):
    """_summary_: filtra os produtos para um intervalo de datas baseado na data de referência, com fallback opcional para o intervalo mais recente disponível

    Args:
        query (_type_): _description_: consulta SQLAlchemy para filtrar
        days (int): _description_: número de dias para o intervalo (ex: 30, 90, 180, 365)

    Returns:
        _type_: _description_: uma tupla contendo a consulta filtrada para o intervalo de datas, a data de referência usada para o filtro, e um booleano indicando se o fallback foi aplicado (True se o intervalo original não tinha dados e foi necessário usar o intervalo mais recente disponível)
    """
    fallback_enabled = _env_bool("ANALYTICS_FALLBACK_TO_LATEST_DATA", False)
    session = query.session
    reference_date = get_reference_date(session)
    cutoff_date = reference_date - timedelta(days=days - 1)

    current_query = query.filter(Product.date >= cutoff_date, Product.date <= reference_date)
    current_count = current_query.with_entities(func.count(Product.id)).scalar() or 0
    if current_count > 0:
        return current_query, reference_date, False

    if not fallback_enabled:       
        return current_query, reference_date, False

    latest_date = (
        session.query(func.max(Product.date))
        .filter(Product.is_synthetic == False)
        .scalar()
    )
    
    if latest_date is None or latest_date == reference_date:
        return current_query, reference_date, False

    fallback_cutoff = latest_date - timedelta(days=days - 1)
    fallback_query = query.filter(Product.date >= fallback_cutoff, Product.date <= latest_date)
    return fallback_query, latest_date, True