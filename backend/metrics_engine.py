import uuid
from backend.db import SessionLocal
from backend.models.product import Product
from sqlalchemy import func


def get_total_revenue(period: str = "all", category: str = "all", region: str = "all", status: str = "all", search: str = "", trace_id: str = None):
    """
    Calcula o total de receita (SUM) com rastreabilidade e contrato padronizado.
    Não altera o resultado legacy, apenas adiciona rastreabilidade e metadados.
    """
    db = SessionLocal()
    if not trace_id:
        trace_id = str(uuid.uuid4())
    try:
        query = db.query(func.sum(Product.revenue))
        if period != "all":
            from datetime import datetime, timedelta
            days_map = {"30d": 30, "90d": 90, "180d": 180, "365d": 365}
            days = days_map.get(period, 365)
            min_date = datetime.now().date() - timedelta(days=days)
            query = query.filter(Product.date >= min_date)
        if category != "all":
            query = query.filter(Product.category == category)
        if region != "all":
            query = query.filter(Product.region == region)
        if status != "all":
            query = query.filter(Product.status == status)
        if search:
            search_term = f"%{search.strip().lower()}%"
            query = query.filter(
                Product.client.ilike(search_term) |
                Product.category.ilike(search_term) |
                Product.region.ilike(search_term)
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
