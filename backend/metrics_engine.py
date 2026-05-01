import uuid

from sqlalchemy import func

from backend.db import SessionLocal
from backend.models.product import Product


def get_total_revenue(period: str = "all", category: str = "all", region: str = "all", status: str = "all", search: str = "", trace_id: str = None):
    """_summary_: Calcula a soma de `revenue` com filtros opcionais.

    Args:
        period (str, optional): _description_. Intervalo (`30d`, `90d`, `180d`, `365d` ou `all`). Defaults to "all".
        category (str, optional): _description_. Categoria especifica ou `all`. Defaults to "all".
        region (str, optional): _description_. Campo legado e ignorado na consulta. Defaults to "all".
        status (str, optional): _description_. Status especifico ou `all`. Defaults to "all".
        search (str, optional): _description_. Busca textual parcial em `client` e `category`. Defaults to "".
        trace_id (str, optional): _description_. Identificador de rastreio para resposta/log. Defaults to None.

    Returns:
        _type_: _description_: Dicionario com `value`, `state`, `trace_id`, metadados do calculo e periodo aplicado.
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
                Product.client.ilike(search_term)
                | Product.category.ilike(search_term)
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
                "period": period,
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
                "period": period,
            }
        return {
            "value": float(result),
            "state": "valid",
            "trace_id": trace_id,
            "backend_function": "metrics_engine.get_total_revenue",
            "calculation": "SUM",
            "source": "products.revenue",
            "period": period,
        }
    except Exception:
        return {
            "value": None,
            "state": "error",
            "trace_id": trace_id,
            "backend_function": "metrics_engine.get_total_revenue",
            "calculation": "SUM",
            "source": "products.revenue",
            "period": period,
        }
    finally:
        db.close()
