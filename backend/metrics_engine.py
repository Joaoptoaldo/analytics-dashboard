import uuid
from backend.db import SessionLocal
from backend.models.product import Product
from sqlalchemy import func


def get_total_revenue(period: str = "all", category: str = "all", region: str = "all", status: str = "all", search: str = "", trace_id: str = None):
    """_summary_: método para calcular a receita total a partir dos dados do banco, aplicando os filtros de período, categoria, região, status e busca. O método retorna um dicionário contendo o valor da receita total, o estado do resultado (válido, sem dados ou erro), um trace_id para rastreamento, e metadados sobre a função de backend, cálculo realizado, fonte dos dados e período aplicado.

    Args:
        period (str, optional): _description_. Defaults to "all".: 30d, 90d, 180d, 365d ou all
        category (str, optional): _description_. Defaults to "all".: Electronics, Clothing, Home, Sports ou all
        region (str, optional): _description_. Defaults to "all".: North, South, East, West ou all (DEPRECATED)
        status (str, optional): _description_. Defaults to "all".: active, inactive, pending ou all
        search (str, optional): _description_. Defaults to "".: termo de busca para client ou category
        trace_id (str, optional): _description_. Defaults to None.: identificador único para rastreamento da requisição, se não fornecido, será gerado um novo UUID.

    Returns:
        _type_: _description_: dicionário contendo o valor da receita total, o estado do resultado (válido, sem dados ou erro), um trace_id para rastreamento, e metadados sobre a função de backend, cálculo realizado, fonte dos dados e período aplicado. O campo "value" contém a receita total calculada ou None em caso de erro ou ausência de dados. O campo "state" indica se o resultado é "valid", "no_data" ou "error". Os campos "backend_function", "calculation", "source" e "period" fornecem informações adicionais sobre a origem e natureza do cálculo realizado
    """
    db = SessionLocal()
    if not trace_id:
        trace_id = str(uuid.uuid4())
    try:
        query = db.query(func.sum(Product.revenue)).filter(Product.date != None)
        if period != "all":
            from datetime import datetime, timedelta
            days_map = {"30d": 30, "90d": 90, "180d": 180, "365d": 365}
            days = days_map.get(period, 365)
            min_date = datetime.now().date() - timedelta(days=days)
            query = query.filter(Product.date >= min_date)
        if category != "all":
            query = query.filter(Product.category == category)
        if region != "all":
            import logging

            logging.warning("[DEPRECATED] region filter ignored")
        if status != "all":
            query = query.filter(Product.status == status)
        if search:
            search_term = f"%{search.strip().lower()}%"
            query = query.filter(
                Product.client.ilike(search_term) |
                Product.category.ilike(search_term)
            )
        result = query.scalar()
        if result is None:
            return {
                "value": None,
                "state": "no_data",
                "trace_id": trace_id,
                "backend_function": "metrics_engine.get_total_revenue",
                "calculation": "SUM",
                "source": "products.revenue",
                "period": period
            }
        if result != result or result == float("inf") or result == float("-inf"):
            # NaN ou infinito
            return {
                "value": None,
                "state": "error",
                "trace_id": trace_id,
                "backend_function": "metrics_engine.get_total_revenue",
                "calculation": "SUM",
                "source": "products.revenue",
                "period": period
            }
        return {
            "value": float(result),
            "state": "valid",
            "trace_id": trace_id,
            "backend_function": "metrics_engine.get_total_revenue",
            "calculation": "SUM",
            "source": "products.revenue",
            "period": period
        }
    except Exception:
        return {
            "value": None,
            "state": "error",
            "trace_id": trace_id,
            "backend_function": "metrics_engine.get_total_revenue",
            "calculation": "SUM",
            "source": "products.revenue",
            "period": period
        }
    finally:
        db.close()
